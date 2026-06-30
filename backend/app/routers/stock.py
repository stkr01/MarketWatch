from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Ticker
from app.schemas import TickerResponse
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
