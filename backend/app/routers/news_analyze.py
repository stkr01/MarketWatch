"""News Analyser: paste a URL (or text) → Swedish AI summary + affected assets."""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ticker, NewsAnalysis
from app.config import settings
from app.collectors.article import fetch_article
from app.ai.news_analyzer import analyze_news

router = APIRouter()
logger = logging.getLogger(__name__)


class NewsAnalyzeRequest(BaseModel):
    url: str | None = None
    text: str | None = None
    title: str | None = None  # supplied when a client sends pre-extracted text


@router.post("/news/analyze")
async def news_analyze(payload: NewsAnalyzeRequest, db: Session = Depends(get_db)):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API not configured")

    title = (payload.title or "").strip() or None
    text = (payload.text or "").strip()

    # No pasted text → try to fetch the URL. On failure, 422 so the UI can
    # prompt the user to paste the text instead.
    if not text:
        if not payload.url:
            raise HTTPException(status_code=400, detail="Ange en URL eller klistra in text.")
        result = fetch_article(payload.url.strip())
        if not result["ok"]:
            raise HTTPException(status_code=422, detail=result["error"])
        text, title = result["text"], result.get("title")

    if len(text) < 80:
        raise HTTPException(status_code=400, detail="Texten är för kort för att analysera.")

    watchlist = {
        t.symbol for t in db.query(Ticker)
        .filter(Ticker.is_active == True).all()  # noqa: E712
    }

    try:
        result = analyze_news(text[:12000], title, watchlist)
    except Exception as e:
        logger.error(f"News analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysen misslyckades: {e}")

    assets = result.get("assets", [])
    for a in assets:
        a["on_watchlist"] = a["symbol"] in watchlist

    result["title"] = title
    result["source_url"] = payload.url

    # Persist the analysis so it can be browsed later (history / "step two").
    impact_max = max((a.get("impact_score", 0) for a in assets), default=0)
    record = NewsAnalysis(
        source_url=(payload.url or "").strip() or None,
        title=title,
        summary=result.get("summary", ""),
        overall=result.get("overall", ""),
        assets=json.dumps(assets, ensure_ascii=False),
        impact_max=impact_max,
        usage_tokens=result.get("usage_tokens"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    result["id"] = record.id
    result["created_at"] = record.created_at.isoformat()
    return result


@router.get("/news/analyze/history")
async def news_history(limit: int = 30, db: Session = Depends(get_db)):
    """List saved analyses, newest first (summary metadata only)."""
    rows = (
        db.query(NewsAnalysis)
        .order_by(desc(NewsAnalysis.created_at))
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "source_url": r.source_url,
            "summary": r.summary,
            "impact_max": r.impact_max or 0,
            "asset_count": len(json.loads(r.assets or "[]")),
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/news/analyze/history/{item_id}")
async def news_history_item(item_id: int, db: Session = Depends(get_db)):
    """Return a single saved analysis in full (same shape as a fresh analysis)."""
    r = db.get(NewsAnalysis, item_id)
    if not r:
        raise HTTPException(status_code=404, detail="Analysen hittades inte.")

    assets = json.loads(r.assets or "[]")
    watchlist = {
        t.symbol for t in db.query(Ticker)
        .filter(Ticker.is_active == True).all()  # noqa: E712
    }
    for a in assets:
        a["on_watchlist"] = a.get("symbol") in watchlist

    return {
        "id": r.id,
        "title": r.title,
        "source_url": r.source_url,
        "summary": r.summary,
        "overall": r.overall,
        "assets": assets,
        "usage_tokens": r.usage_tokens,
        "created_at": r.created_at.isoformat(),
    }


@router.delete("/news/analyze/history/{item_id}")
async def delete_news_history_item(item_id: int, db: Session = Depends(get_db)):
    """Delete a saved analysis."""
    r = db.get(NewsAnalysis, item_id)
    if not r:
        raise HTTPException(status_code=404, detail="Analysen hittades inte.")
    db.delete(r)
    db.commit()
    return {"ok": True, "id": item_id}
