from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Ticker, NewsItem
from app.schemas import NewsItemResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/news/{ticker}", response_model=list[NewsItemResponse])
async def get_stock_news(ticker: str, db: Session = Depends(get_db)):
    """Get recent news for a stock (sorted by recency)"""
    ticker_upper = ticker.upper()

    ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker_upper).first()

    if not ticker_obj:
        logger.warning(f"Ticker not found: {ticker}")
        return []

    news_items = db.query(NewsItem).filter(
        NewsItem.ticker_id == ticker_obj.id
    ).order_by(desc(NewsItem.published_at)).limit(20).all()

    logger.info(f"Retrieved {len(news_items)} news items for {ticker}")
    return [NewsItemResponse.from_orm(item) for item in news_items]
