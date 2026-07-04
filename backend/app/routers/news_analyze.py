"""News Analyser: paste a URL (or text) → Swedish AI summary + affected assets."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ticker
from app.config import settings
from app.collectors.article import fetch_article
from app.ai.news_analyzer import analyze_news

router = APIRouter()
logger = logging.getLogger(__name__)


class NewsAnalyzeRequest(BaseModel):
    url: str | None = None
    text: str | None = None


@router.post("/news/analyze")
async def news_analyze(payload: NewsAnalyzeRequest, db: Session = Depends(get_db)):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API not configured")

    title = None
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

    for a in result.get("assets", []):
        a["on_watchlist"] = a["symbol"] in watchlist

    result["title"] = title
    result["source_url"] = payload.url
    return result
