"""Live ticker-tape endpoint — the scrolling banner at the top of the dashboard.

Shows the major indices, EUR/USD, and every active watchlist symbol with its
current price and change vs. the prior close. Prices come from yfinance via a
single batched fetch, wrapped in a small stale-while-revalidate cache so the
endpoint always answers instantly (the banner is polled frequently by every
open tab) while refreshing at most once per TTL in the background.
"""
from datetime import datetime, timezone
import threading
import time
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Ticker
from app.collectors.ticker_tape import get_tape_quotes
from app.schemas import TickerTapeResponse, TapeQuote

router = APIRouter()
logger = logging.getLogger(__name__)

# Fixed market symbols shown before the watchlist. (symbol, label, kind)
MARKET_SYMBOLS: list[tuple[str, str, str]] = [
    ("^GSPC", "S&P 500", "index"),
    ("^IXIC", "Nasdaq", "index"),
    ("^DJI", "Dow Jones", "index"),
    ("^RUT", "Russell 2000", "index"),
    ("^VIX", "VIX", "index"),
    ("EURUSD=X", "EUR/USD", "fx"),
]

# Refresh the tape at most this often. The scan runs every 5 min; a shorter
# tape TTL keeps the banner livelier without hammering yfinance.
TTL_SECONDS = 60

_cache: dict = {"quotes": {}, "ts": 0.0, "symbols": []}
_lock = threading.Lock()
_refreshing = False


def _refresh(symbols: list[str]) -> None:
    global _refreshing
    try:
        quotes = get_tape_quotes(symbols)
        with _lock:
            # Only overwrite if we actually got data, so a transient yfinance
            # failure doesn't blank out a good tape.
            if quotes:
                _cache["quotes"] = quotes
                _cache["ts"] = time.time()
                _cache["symbols"] = symbols
    finally:
        with _lock:
            _refreshing = False


def _maybe_refresh(symbols: list[str]) -> None:
    """Kick a refresh if the cache is stale, empty, or the symbol set changed.

    A cold cache or a changed watchlist refreshes synchronously (we have nothing
    good to serve); a merely-stale cache refreshes in the background and serves
    the previous values immediately.
    """
    global _refreshing
    do_sync = False
    do_bg = False
    now = time.time()
    with _lock:
        stale = (now - _cache["ts"]) > TTL_SECONDS
        empty_or_changed = (not _cache["quotes"]) or symbols != _cache["symbols"]
        if (stale or empty_or_changed) and not _refreshing:
            _refreshing = True
            if empty_or_changed:
                do_sync = True
            else:
                do_bg = True
    if do_sync:
        _refresh(symbols)
    elif do_bg:
        threading.Thread(target=_refresh, args=(symbols,), daemon=True).start()


@router.get("/ticker-tape", response_model=TickerTapeResponse)
async def ticker_tape(db: Session = Depends(get_db)):
    """Ordered quotes for the banner: indices + FX first, then the watchlist."""
    watch = [
        t.symbol
        for t in db.query(Ticker)
        .filter(Ticker.is_active == True)  # noqa: E712
        .order_by(Ticker.symbol)
        .all()
    ]

    entries = list(MARKET_SYMBOLS) + [(s, s, "watchlist") for s in watch]
    symbols = [s for s, _, _ in entries]

    _maybe_refresh(symbols)

    with _lock:
        quotes = dict(_cache["quotes"])
        ts = _cache["ts"]

    result = []
    for symbol, label, kind in entries:
        q = quotes.get(symbol)
        result.append(TapeQuote(
            symbol=symbol,
            label=label,
            kind=kind,
            price=q["price"] if q else None,
            change=q["change"] if q else None,
            change_pct=q["change_pct"] if q else None,
        ))

    as_of = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
    return TickerTapeResponse(as_of=as_of, quotes=result)
