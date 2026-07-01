from fastapi import APIRouter
from app.schemas import OutcomesResponse
from app.outcomes import get_outcomes_summary
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/outcomes", response_model=OutcomesResponse)
async def get_outcomes():
    """Screener performance: win rate & average returns of flagged candidates."""
    return get_outcomes_summary()
