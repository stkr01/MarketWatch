from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Scan, ScanResult, Ticker
from app.schemas import CandidateResponse, TickerResponse, ScanResultResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/candidates", response_model=list[CandidateResponse])
async def get_candidates(db: Session = Depends(get_db)):
    """
    Get list of current swing trading candidates

    Returns latest scan results that passed screening rules
    """
    # Get the most recent scan
    latest_scan = db.query(Scan).order_by(desc(Scan.timestamp)).first()

    if not latest_scan:
        logger.info("No scans found in database")
        return []

    # Get scan results from latest scan that passed screening rules
    scan_results = db.query(ScanResult).filter(
        ScanResult.scan_id == latest_scan.id,
        ScanResult.is_candidate == True
    ).all()

    candidates = []

    for result in scan_results:
        ticker = result.ticker

        # Build response
        candidate = CandidateResponse(
            ticker=TickerResponse(
                id=ticker.id,
                symbol=ticker.symbol,
                name=ticker.name,
                exchange=ticker.exchange,
                market_cap=ticker.market_cap,
                last_updated=ticker.last_updated
            ),
            scan_result=ScanResultResponse(
                id=result.id,
                ticker_id=result.ticker_id,
                gap_pct=result.gap_pct,
                volume=result.volume,
                volume_avg_20=result.volume_avg_20,
                rvol=result.rvol,
                price=result.price,
                previous_close=result.previous_close,
                pre_market_price=result.pre_market_price,
                price_source=result.price_source,
                ema_100=result.ema_100,
                above_ema_100=result.above_ema_100,
                rsi_14=result.rsi_14,
                atr_14=result.atr_14,
                atr_pct=result.atr_pct,
                has_news=result.has_news,
                timestamp=result.timestamp,
                ticker=TickerResponse(
                    id=ticker.id,
                    symbol=ticker.symbol,
                    name=ticker.name,
                    exchange=ticker.exchange,
                    market_cap=ticker.market_cap,
                    last_updated=ticker.last_updated
                )
            ),
            has_news=result.has_news,
            latest_analysis=None  # TODO: Get latest AI analysis if exists
        )
        candidates.append(candidate)

    logger.info(f"Returning {len(candidates)} candidates from scan {latest_scan.id}")
    return candidates
