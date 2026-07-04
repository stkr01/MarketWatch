"""Market-movers discovery endpoint (auto-found via Yahoo screeners)."""
from datetime import datetime, timezone
import threading
import time
import logging

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Ticker
from app.collectors.movers import get_movers

router = APIRouter()
logger = logging.getLogger(__name__)

# Movers shift slowly and screen() is a few network calls; cache a bit longer.
TTL_SECONDS = 180
_cache: dict = {"movers": [], "ts": 0.0}
_lock = threading.Lock()
_refreshing = False


def _refresh() -> None:
    global _refreshing
    try:
        movers = get_movers()
        with _lock:
            if movers:
                _cache["movers"] = movers
                _cache["ts"] = time.time()
    finally:
        with _lock:
            _refreshing = False


def _maybe_refresh() -> None:
    global _refreshing
    do_sync = do_bg = False
    now = time.time()
    with _lock:
        stale = (now - _cache["ts"]) > TTL_SECONDS
        empty = not _cache["movers"]
        if (stale or empty) and not _refreshing:
            _refreshing = True
            do_sync = empty
            do_bg = not empty
    if do_sync:
        _refresh()
    elif do_bg:
        threading.Thread(target=_refresh, daemon=True).start()


def _watchlist_symbols() -> set[str]:
    db: Session = SessionLocal()
    try:
        return {
            t.symbol for t in db.query(Ticker)
            .filter(Ticker.is_active == True).all()  # noqa: E712
        }
    finally:
        db.close()


@router.get("/movers")
async def movers():
    """Top auto-discovered movers, flagged if already on the watchlist."""
    _maybe_refresh()
    with _lock:
        items = list(_cache["movers"])
        ts = _cache["ts"]

    on_watchlist = _watchlist_symbols()
    for m in items:
        m["on_watchlist"] = m["symbol"] in on_watchlist

    as_of = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None
    return {"as_of": as_of, "movers": items}
