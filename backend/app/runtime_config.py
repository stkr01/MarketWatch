"""Runtime-adjustable settings.

A handful of thresholds can be changed live from the dashboard instead of by
editing `.env` and restarting. Overrides are persisted in the `app_settings`
table and cached in memory; everything not overridden falls back to the
env-based defaults in `settings`.
"""
import logging
from threading import Lock

from app.config import settings
from app.db import SessionLocal
from app.models import AppSetting

logger = logging.getLogger(__name__)

# Tunables the UI is allowed to edit. `default` is pulled from the env config.
TUNABLES: dict[str, dict] = {
    "GAP_THRESHOLD_PERCENT": {
        "label": "Screening gap threshold",
        "help": "Minimum |gap %| for a stock to become a candidate",
        "default": settings.GAP_THRESHOLD_PERCENT,
        "min": 0.0, "max": 20.0, "step": 0.5, "unit": "%",
    },
    "ALERT_GAP_THRESHOLD_PERCENT": {
        "label": "Alert gap threshold",
        "help": "Minimum |gap %| for a candidate to trigger a Telegram alert",
        "default": settings.ALERT_GAP_THRESHOLD_PERCENT,
        "min": 0.0, "max": 20.0, "step": 0.5, "unit": "%",
    },
}

_cache: dict[str, float] = {}
_lock = Lock()


def load() -> None:
    """Load persisted overrides from the DB into the in-memory cache."""
    db = SessionLocal()
    try:
        rows = db.query(AppSetting).all()
        with _lock:
            _cache.clear()
            for row in rows:
                if row.key in TUNABLES:
                    try:
                        _cache[row.key] = float(row.value)
                    except (TypeError, ValueError):
                        logger.warning(f"Ignoring non-numeric setting {row.key}={row.value!r}")
        if _cache:
            logger.info(f"Loaded runtime setting overrides: {_cache}")
    finally:
        db.close()


def get_float(key: str) -> float:
    """Current value for a tunable: the override if set, else the env default."""
    with _lock:
        if key in _cache:
            return _cache[key]
    return float(TUNABLES[key]["default"])


def set_value(key: str, value: float) -> float:
    """Validate + clamp to bounds, persist, and cache. Returns the stored value."""
    if key not in TUNABLES:
        raise KeyError(key)
    spec = TUNABLES[key]
    v = round(max(spec["min"], min(spec["max"], float(value))), 4)

    db = SessionLocal()
    try:
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        if row:
            row.value = str(v)
        else:
            db.add(AppSetting(key=key, value=str(v)))
        db.commit()
    finally:
        db.close()

    with _lock:
        _cache[key] = v
    logger.info(f"Setting {key} updated to {v}")
    return v


def snapshot() -> list[dict]:
    """All tunables with current + default values and bounds (for the UI)."""
    return [
        {
            "key": key,
            "label": spec["label"],
            "help": spec["help"],
            "value": get_float(key),
            "default": float(spec["default"]),
            "min": spec["min"],
            "max": spec["max"],
            "step": spec["step"],
            "unit": spec["unit"],
        }
        for key, spec in TUNABLES.items()
    ]
