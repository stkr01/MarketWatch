from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import NewsItemResponse

router = APIRouter()


@router.get("/news/{ticker}", response_model=list[NewsItemResponse])
async def get_stock_news(ticker: str, db: Session = Depends(get_db)):
    """Get recent news for a stock"""
    # TODO: Implement
    return []
