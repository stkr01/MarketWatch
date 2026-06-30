from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Ticker, ScanResult, NewsItem, AIAnalysis
from app.schemas import AIAnalysisResponse
from app.ai.claude_analyzer import analyze_stock_candidate
from app.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stock/{ticker}/analyze", response_model=AIAnalysisResponse)
async def analyze_stock(ticker: str, db: Session = Depends(get_db)):
    """
    Request Claude AI analysis for a specific stock

    Fetches latest scan result + recent news, runs Claude analysis,
    and caches result in database
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured")
        raise HTTPException(status_code=500, detail="Claude API not configured")

    ticker_upper = ticker.upper()

    # Get ticker
    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()
    if not ticker_obj:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Get latest scan result for this ticker
    scan_result = db.query(ScanResult).filter(
        ScanResult.ticker_id == ticker_obj.id
    ).order_by(desc(ScanResult.timestamp)).first()

    if not scan_result:
        raise HTTPException(status_code=404, detail=f"No scan data for {ticker}")

    # Get recent news
    news_items = db.query(NewsItem).filter(
        NewsItem.ticker_id == ticker_obj.id
    ).order_by(desc(NewsItem.published_at)).limit(5).all()

    news_dicts = [
        {
            "title": n.title,
            "source": n.source,
            "url": n.url,
            "published_at": n.published_at
        }
        for n in news_items
    ]

    # Build market data dict for Claude
    market_data = {
        "gap_pct": scan_result.gap_pct,
        "volume": scan_result.volume,
        "volume_avg_20": scan_result.volume_avg_20,
        "price": scan_result.price,
        "ema_100": scan_result.ema_100,
        "above_ema_100": scan_result.above_ema_100
    }

    try:
        logger.info(f"Requesting Claude analysis for {ticker}")

        # Call Claude API
        claude_result = analyze_stock_candidate(
            ticker=ticker_upper,
            market_data=market_data,
            news_items=news_dicts
        )

        # Save analysis to database
        analysis = AIAnalysis(
            ticker_id=ticker_obj.id,
            response=claude_result["response"],
            usage_tokens=claude_result.get("usage_tokens"),
            prompt_version="v1"
        )
        db.add(analysis)
        db.commit()

        logger.info(f"Analysis saved for {ticker}")

        return AIAnalysisResponse.from_orm(analysis)

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
