from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Ticker, ScanResult, NewsItem, AIAnalysis
from app.schemas import AIAnalysisResponse
from app.ai.claude_analyzer import analyze_stock_candidate, explain_gap, generate_trade_plan
from app.collectors.market_data import get_market_data
from app.config import settings
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def _latest_scan_and_news(ticker: str, db: Session):
    """Shared lookup: ticker row, its latest scan result, and recent news dicts."""
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API not configured")

    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker.upper()).first()
    if not ticker_obj:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    scan_result = db.query(ScanResult).filter(
        ScanResult.ticker_id == ticker_obj.id
    ).order_by(desc(ScanResult.timestamp)).first()
    if not scan_result:
        raise HTTPException(status_code=404, detail=f"No scan data for {ticker}")

    news_items = db.query(NewsItem).filter(
        NewsItem.ticker_id == ticker_obj.id
    ).order_by(desc(NewsItem.published_at)).limit(6).all()
    news_dicts = [{"title": n.title, "source": n.source} for n in news_items]

    return ticker_obj, scan_result, news_dicts


def _market_data(scan_result) -> dict:
    return {
        "gap_pct": scan_result.gap_pct,
        "price": scan_result.price,
        "rvol": scan_result.rvol,
        "rsi_14": scan_result.rsi_14,
        "atr_14": scan_result.atr_14,
        "above_ema_100": scan_result.above_ema_100,
    }


def _compute_levels(scan_result) -> dict:
    """ATR-based entry/stop/target at a fixed 2R, biased by gap direction."""
    price = scan_result.price
    atr = scan_result.atr_14 or round(price * 0.02, 4)   # fallback: 2% of price
    long_bias = scan_result.gap_pct >= 0
    if long_bias:
        entry, stop, target = price, price - atr, price + 2 * atr
    else:
        entry, stop, target = price, price + atr, price - 2 * atr
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return {
        "direction": "long" if long_bias else "short",
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "target": round(target, 2),
        "risk": round(risk, 2),
        "reward": round(reward, 2),
        "rr": round(reward / risk, 1) if risk else None,
        "atr_used": round(atr, 2),
    }


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

    # Ticker may not be in the DB at all (e.g. a Market Mover pulled live from
    # Yahoo that was never scanned). We still want to analyze it, so treat a
    # missing ticker/scan as "fetch live data on demand" instead of a 404.
    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()

    scan_result = None
    if ticker_obj:
        scan_result = db.query(ScanResult).filter(
            ScanResult.ticker_id == ticker_obj.id
        ).order_by(desc(ScanResult.timestamp)).first()

    if scan_result:
        # Use the persisted scan + any stored news for this ticker.
        news_items = db.query(NewsItem).filter(
            NewsItem.ticker_id == ticker_obj.id
        ).order_by(desc(NewsItem.published_at)).limit(5).all()
        news_dicts = [
            {
                "title": n.title,
                "source": n.source,
                "url": n.url,
                "published_at": n.published_at,
            }
            for n in news_items
        ]
        market_data = {
            "gap_pct": scan_result.gap_pct,
            "volume": scan_result.volume,
            "volume_avg_20": scan_result.volume_avg_20,
            "price": scan_result.price,
            "ema_100": scan_result.ema_100,
            "above_ema_100": scan_result.above_ema_100,
        }
    else:
        # On-demand: compute a live snapshot for an un-scanned ticker.
        logger.info(f"No scan data for {ticker}; fetching live market data on demand")
        live = get_market_data(ticker_upper)
        if not live:
            raise HTTPException(
                status_code=404,
                detail=f"Ingen marknadsdata hittades för {ticker}",
            )
        news_dicts = []  # no stored news for an un-added ticker
        market_data = {
            "gap_pct": live["gap_pct"],
            "volume": live["volume"],
            "volume_avg_20": live["volume_avg_20"],
            "price": live["price"],
            "ema_100": live["ema_100"],
            "above_ema_100": live["above_ema_100"],
        }

    try:
        logger.info(f"Requesting Claude analysis for {ticker}")

        # Call Claude API
        claude_result = analyze_stock_candidate(
            ticker=ticker_upper,
            market_data=market_data,
            news_items=news_dicts
        )

        # Persist only when the ticker exists in the DB (AIAnalysis.ticker_id is
        # a FK). Un-added movers get an ephemeral, non-persisted result.
        if ticker_obj:
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

        logger.info(f"Returning ephemeral (live) analysis for {ticker}")
        return AIAnalysisResponse(
            id=0,
            ticker_id=0,
            requested_at=datetime.utcnow(),
            prompt_version="v1-live",
            response=claude_result["response"],
            usage_tokens=claude_result.get("usage_tokens"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/stock/{ticker}/why")
async def why_gapping(ticker: str, db: Session = Depends(get_db)):
    """Claude's take on the most likely reason this ticker is gapping."""
    _, scan_result, news_dicts = _latest_scan_and_news(ticker, db)
    try:
        result = explain_gap(ticker.upper(), _market_data(scan_result), news_dicts)
        return result
    except Exception as e:
        logger.error(f"why_gapping failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.post("/stock/{ticker}/trade-plan")
async def trade_plan(ticker: str, db: Session = Depends(get_db)):
    """ATR-based entry/stop/target levels plus a Claude-written trade plan."""
    _, scan_result, _ = _latest_scan_and_news(ticker, db)
    levels = _compute_levels(scan_result)
    try:
        plan = generate_trade_plan(ticker.upper(), _market_data(scan_result), levels)
        return {**levels, "ticker": ticker.upper(),
                "plan": plan["response"], "usage_tokens": plan["usage_tokens"]}
    except Exception as e:
        logger.error(f"trade_plan failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Trade plan failed: {str(e)}")
