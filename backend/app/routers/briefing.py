from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from app.db import get_db
from app.models import Briefing, Scan, ScanResult, Ticker
from app.schemas import BriefingResponse
from app.ai.briefing import generate_briefing
from app.collectors.economic_calendar import get_us_calendar_today
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")


def _today_et() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def _latest_candidates(db: Session) -> list[dict]:
    """Metrics for candidates from the most recent scan."""
    latest = db.query(Scan).order_by(desc(Scan.timestamp)).first()
    if not latest:
        return []

    rows = (
        db.query(ScanResult, Ticker)
        .join(Ticker, ScanResult.ticker_id == Ticker.id)
        .filter(ScanResult.scan_id == latest.id, ScanResult.is_candidate == True)  # noqa: E712
        .all()
    )
    return [
        {
            "symbol": t.symbol,
            "gap_pct": sr.gap_pct,
            "rvol": sr.rvol,
            "rsi_14": sr.rsi_14,
            "above_ema_100": sr.above_ema_100,
            "has_news": sr.has_news,
        }
        for sr, t in rows
    ]


@router.get("/briefing", response_model=BriefingResponse)
async def get_briefing(db: Session = Depends(get_db)):
    """Return today's cached morning briefing (content null if not generated)."""
    today = _today_et()
    b = db.query(Briefing).filter(Briefing.date == today).first()
    if not b:
        return BriefingResponse(date=today, content=None)
    return BriefingResponse(
        date=b.date, content=b.content, generated_at=b.generated_at, usage_tokens=b.usage_tokens
    )


@router.get("/briefing/history", response_model=list[BriefingResponse])
async def briefing_history(limit: int = 30, db: Session = Depends(get_db)):
    """Past morning briefings, newest first (one per calendar day)."""
    rows = (
        db.query(Briefing)
        .order_by(desc(Briefing.date))
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return [
        BriefingResponse(
            date=b.date, content=b.content,
            generated_at=b.generated_at, usage_tokens=b.usage_tokens,
        )
        for b in rows
    ]


def generate_and_store_briefing(db: Session) -> Briefing:
    """Generate today's morning briefing via Claude and upsert it (one row per ET day).

    Shared by the POST endpoint and the overnight scheduler job. Raises on failure;
    callers translate that into an HTTP error or a logged scheduler error.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("Claude API not configured")

    candidates = _latest_candidates(db)
    econ_events = get_us_calendar_today()

    result = generate_briefing(candidates, econ_events)

    today = _today_et()
    b = db.query(Briefing).filter(Briefing.date == today).first()
    if b:
        b.content = result["content"]
        b.generated_at = datetime.utcnow()
        b.usage_tokens = result["usage_tokens"]
    else:
        b = Briefing(
            date=today,
            content=result["content"],
            usage_tokens=result["usage_tokens"],
        )
        db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.post("/briefing/generate", response_model=BriefingResponse)
async def create_briefing(db: Session = Depends(get_db)):
    """Generate (or regenerate) today's morning briefing via Claude."""
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API not configured")

    try:
        b = generate_and_store_briefing(db)
    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Briefing failed: {e}")

    return BriefingResponse(
        date=b.date, content=b.content, generated_at=b.generated_at, usage_tokens=b.usage_tokens
    )
