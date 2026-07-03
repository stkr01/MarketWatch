from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from app import runtime_config

router = APIRouter()
logger = logging.getLogger(__name__)


class SettingUpdate(BaseModel):
    key: str
    value: float


@router.get("/settings")
async def get_settings():
    """Current runtime-adjustable settings with defaults and bounds."""
    return {"settings": runtime_config.snapshot()}


@router.patch("/settings")
async def update_setting(update: SettingUpdate):
    """Update one tunable; value is clamped to its allowed range."""
    try:
        value = runtime_config.set_value(update.key, update.value)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown setting '{update.key}'")
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Value must be numeric")
    return {"key": update.key, "value": value}
