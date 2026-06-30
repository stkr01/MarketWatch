from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ScanStatusResponse

router = APIRouter()


@router.get("/scan/status", response_model=ScanStatusResponse)
async def get_scan_status(db: Session = Depends(get_db)):
    """Get current scan status and next scheduled scan"""
    # TODO: Implement
    return ScanStatusResponse()


@router.post("/scan")
async def trigger_scan(db: Session = Depends(get_db)):
    """Manually trigger a market scan"""
    # TODO: Implement
    return {"status": "scan started"}
