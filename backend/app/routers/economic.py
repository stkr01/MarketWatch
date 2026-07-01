from fastapi import APIRouter
from app.schemas import EconomicEventResponse
from app.collectors.economic_calendar import get_us_calendar_today
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/economic-calendar", response_model=list[EconomicEventResponse])
async def get_economic_calendar():
    """Get today's US (USD) economic calendar events, sorted by time."""
    return get_us_calendar_today()
