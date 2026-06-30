from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import AIAnalysisResponse

router = APIRouter()


@router.post("/stock/{ticker}/analyze", response_model=AIAnalysisResponse)
async def analyze_stock(ticker: str, db: Session = Depends(get_db)):
    """Request Claude AI analysis for a specific stock"""
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Stock not found")
