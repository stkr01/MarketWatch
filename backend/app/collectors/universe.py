"""Ticker universe for scanning — backed by the DB watchlist."""
import logging
from app.config import settings
from app.db import SessionLocal
from app.models import Ticker

logger = logging.getLogger(__name__)

# Default seed watchlist — highly liquid names with frequent news coverage.
TOP_TICKERS = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "NVDA",   # NVIDIA
    "TSLA",   # Tesla
    "AMZN",   # Amazon
    "META",   # Meta
    "GOOGL",  # Alphabet
    "NFLX",   # Netflix
    "AMD",    # Advanced Micro Devices
    "MSTR",   # MicroStrategy
]

_NASDAQ = {"AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "NFLX", "AMD", "MSTR"}


def get_ticker_info(ticker: str) -> dict:
    """Basic ticker info (can be enhanced with a metadata API later)."""
    return {
        "symbol": ticker,
        "exchange": "NASDAQ" if ticker in _NASDAQ else "NYSE",
        "name": ticker,
    }


def seed_default_watchlist() -> None:
    """Populate the watchlist with default tickers if the DB has none."""
    db = SessionLocal()
    try:
        if db.query(Ticker).count() > 0:
            return
        logger.info("Seeding default watchlist")
        for sym in TOP_TICKERS:
            info = get_ticker_info(sym)
            db.add(Ticker(symbol=sym, name=info["name"], exchange=info["exchange"], is_active=True))
        db.commit()
    finally:
        db.close()


def get_ticker_universe() -> list[str]:
    """Return the active watchlist symbols to scan (falls back to defaults)."""
    db = SessionLocal()
    try:
        rows = (
            db.query(Ticker)
            .filter(Ticker.is_active == True)  # noqa: E712
            .order_by(Ticker.symbol)
            .all()
        )
        symbols = [r.symbol for r in rows]
    finally:
        db.close()

    if not symbols:
        symbols = TOP_TICKERS[: settings.TOP_N_TICKERS]

    logger.info(f"Ticker universe: {len(symbols)} tickers")
    return symbols
