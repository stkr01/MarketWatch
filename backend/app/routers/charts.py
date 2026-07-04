"""Chart data: intraday history for the detail panel, sparklines for the table."""
from datetime import datetime, timezone
import threading
import time
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ticker
from app.collectors.chart_data import get_history, get_sparklines

router = APIRouter()
logger = logging.getLogger(__name__)

# Sparklines are polled by the candidate table; cache + stale-while-revalidate
# so we hit yfinance at most once per TTL regardless of open tabs.
TTL_SECONDS = 60
_cache: dict = {"series": {}, "ts": 0.0, "symbols": []}
_lock = threading.Lock()
_refreshing = False


def _refresh(symbols: list[str]) -> None:
    global _refreshing
    try:
        series = get_sparklines(symbols)
        with _lock:
            if series:
                _cache["series"] = series
                _cache["ts"] = time.time()
                _cache["symbols"] = symbols
    finally:
        with _lock:
            _refreshing = False


def _maybe_refresh(symbols: list[str]) -> None:
    global _refreshing
    do_sync = do_bg = False
    now = time.time()
    with _lock:
        stale = (now - _cache["ts"]) > TTL_SECONDS
        empty_or_changed = (not _cache["series"]) or symbols != _cache["symbols"]
        if (stale or empty_or_changed) and not _refreshing:
            _refreshing = True
            do_sync = empty_or_changed
            do_bg = not empty_or_changed
    if do_sync:
        _refresh(symbols)
    elif do_bg:
        threading.Thread(target=_refresh, args=(symbols,), daemon=True).start()


@router.get("/sparklines")
async def sparklines(db: Session = Depends(get_db)):
    """Downsampled intraday series keyed by symbol, for the active watchlist."""
    symbols = [
        t.symbol
        for t in db.query(Ticker)
        .filter(Ticker.is_active == True)  # noqa: E712
        .order_by(Ticker.symbol)
        .all()
    ]
    _maybe_refresh(symbols)
    with _lock:
        series = dict(_cache["series"])
        ts = _cache["ts"]
    as_of = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None
    return {"as_of": as_of, "series": series}


@router.get("/stock/{ticker}/history")
async def stock_history(ticker: str):
    """Intraday 1-minute price series (incl. pre/post-market) for the detail chart."""
    return get_history(ticker.upper())
