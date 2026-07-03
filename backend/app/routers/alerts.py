from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from app.db import get_db
from app.models import AlertSent
from app.schemas import AlertsResponse
from app.alerts import alerts_status, send_test_alert

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(db: Session = Depends(get_db)):
    """Alert config summary + recent sent alerts (most recent first)."""
    status = alerts_status()
    rows = (
        db.query(AlertSent)
        .filter(AlertSent.status != "test")
        .order_by(AlertSent.sent_at.desc())
        .limit(30)
        .all()
    )
    return {**status, "alerts": rows}


@router.post("/alerts/test")
async def post_test_alert(db: Session = Depends(get_db)):
    """Send a test notification to all configured channels."""
    return send_test_alert(db)
