from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import TickerResponse

router = APIRouter()


@router.get("/stock/{ticker}", response_model=TickerResponse)
async def get_stock_detail(ticker: str, db: Session = Depends(get_db)):
    """Get detailed stock information"""
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Stock not found")
