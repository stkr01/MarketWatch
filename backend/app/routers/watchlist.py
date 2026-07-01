from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import yfinance as yf
import logging

from app.db import get_db
from app.models import Ticker
from app.schemas import WatchlistItem, WatchlistAdd
from app.collectors.universe import get_ticker_info

router = APIRouter()
logger = logging.getLogger(__name__)


def _symbol_exists(symbol: str) -> bool:
    """Light validation that a ticker resolves to real market data."""
    try:
        data = yf.download(symbol, period="5d", progress=False, threads=False)
        return data is not None and not data.empty
    except Exception as e:
        logger.warning(f"Validation failed for {symbol}: {e}")
        return False


@router.get("/watchlist", response_model=list[WatchlistItem])
async def list_watchlist(db: Session = Depends(get_db)):
    """List the active watchlist tickers that get scanned."""
    rows = (
        db.query(Ticker)
        .filter(Ticker.is_active == True)  # noqa: E712
        .order_by(Ticker.symbol)
        .all()
    )
    return rows


@router.post("/watchlist", response_model=WatchlistItem, status_code=201)
async def add_to_watchlist(payload: WatchlistAdd, db: Session = Depends(get_db)):
    """Add (or reactivate) a ticker in the watchlist."""
    symbol = payload.symbol.strip().upper()
    if not symbol or len(symbol) > 10:
        raise HTTPException(status_code=400, detail="Invalid ticker symbol")

    existing = db.query(Ticker).filter(Ticker.symbol == symbol).first()
    if existing and existing.is_active:
        raise HTTPException(status_code=409, detail=f"{symbol} is already in the watchlist")

    if not _symbol_exists(symbol):
        raise HTTPException(status_code=404, detail=f"No market data found for {symbol}")

    if existing:
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    info = get_ticker_info(symbol)
    ticker = Ticker(symbol=symbol, name=info["name"], exchange=info["exchange"], is_active=True)
    db.add(ticker)
    db.commit()
    db.refresh(ticker)
    logger.info(f"Added {symbol} to watchlist")
    return ticker


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    """Remove a ticker from the watchlist (soft — keeps historical scans)."""
    symbol = symbol.strip().upper()
    ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
    if not ticker or not ticker.is_active:
        raise HTTPException(status_code=404, detail=f"{symbol} is not in the watchlist")

    ticker.is_active = False
    db.commit()
    logger.info(f"Removed {symbol} from watchlist")
    return {"status": "removed", "symbol": symbol}
