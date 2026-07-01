from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Ticker, ScanResult
from app.schemas import TickerResponse, ScanMetricsResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stock/{ticker}", response_model=TickerResponse)
async def get_stock_detail(ticker: str, db: Session = Depends(get_db)):
    """Get detailed stock information"""
    ticker_upper = ticker.upper()
    stock = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()

    if not stock:
        logger.warning(f"Stock not found: {ticker}")
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    logger.info(f"Retrieved stock: {ticker}")
    return TickerResponse.from_orm(stock)


@router.get("/stock/{ticker}/scan", response_model=ScanMetricsResponse)
async def get_stock_scan_metrics(ticker: str, db: Session = Depends(get_db)):
    """Get the most recent scan metrics (gap, RVOL, RSI, ATR, EMA) for a ticker."""
    ticker_upper = ticker.upper()
    stock = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    result = db.query(ScanResult).filter(
        ScanResult.ticker_id == stock.id
    ).order_by(desc(ScanResult.timestamp)).first()

    if not result:
        raise HTTPException(status_code=404, detail=f"No scan metrics for {ticker}")

    return ScanMetricsResponse.from_orm(result)
