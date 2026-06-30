from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import get_db
from app.models import Scan
from app.schemas import ScanStatusResponse
from app.scheduler import trigger_scan_now, get_next_run
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/scan/status", response_model=ScanStatusResponse)
async def get_scan_status(db: Session = Depends(get_db)):
    """Get current scan status and next scheduled scan"""
    last_scan = db.query(Scan).order_by(desc(Scan.timestamp)).first()

    return ScanStatusResponse(
        last_scan=last_scan.timestamp if last_scan else None,
        next_scan=get_next_run(),
        is_running=False
    )


@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    """Manually trigger a market scan in the background"""
    logger.info("Manual scan requested via API")
    background_tasks.add_task(trigger_scan_now)
    return {"status": "scan started", "message": "Scan running in background"}
