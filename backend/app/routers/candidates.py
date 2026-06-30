from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import CandidateResponse

router = APIRouter()


@router.get("/candidates", response_model=list[CandidateResponse])
async def get_candidates(db: Session = Depends(get_db)):
    """Get list of current swing trading candidates"""
    # TODO: Implement
    return []
