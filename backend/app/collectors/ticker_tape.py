"""Batched quote fetching for the live ticker tape (top-of-page banner).

Unlike the full scan (which pulls 1y of history per ticker for indicators), the
tape only needs *last price* + *change vs. prior close* for many symbols at once.
So we do just two batched yfinance downloads regardless of how many symbols there
are: one daily (for the reference close) and one 1-minute/prepost (for the live
price, so indices/FX/watchlist all reflect real pre-market movement).
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")


def _safe_download(symbols: list[str], **kwargs) -> pd.DataFrame | None:
    try:
        return yf.download(
            symbols, progress=False, threads=True, group_by="ticker", **kwargs
        )
    except Exception as e:  # network / yfinance hiccup — tape degrades gracefully
        logger.warning(f"Tape download failed ({kwargs}): {e}")
        return None


def _series_for(frame: pd.DataFrame | None, symbol: str, field: str = "Close") -> pd.Series | None:
    """Pull one field's Series for `symbol` from a yf.download frame.

    yfinance returns a plain column index for a single symbol and a MultiIndex
    for several; with group_by='ticker' the levels are (symbol, field).
    """
    if frame is None or frame.empty:
        return None
    cols = frame.columns
    try:
        if isinstance(cols, pd.MultiIndex):
            if symbol in cols.get_level_values(0):
                s = frame[symbol][field]
            elif symbol in cols.get_level_values(1):        # (field, symbol) layout
                s = frame[field][symbol]
            else:
                return None
        else:
            s = frame[field]
    except (KeyError, IndexError):
        return None
    return s.dropna()


def _prev_close(closes: pd.Series) -> float:
    """Most recent completed regular-session close *before* today (Eastern).

    Same reference the scan uses, so the tape's change% matches the dashboard's
    gap: during pre-market this is yesterday's close, not the in-progress bar.
    """
    today = datetime.now(ET).date()
    prior = [float(c) for idx, c in zip(closes.index, closes)
             if getattr(idx, "date", lambda: None)() and idx.date() < today]
    if prior:
        return prior[-1]
    if len(closes) >= 2:
        return float(closes.iloc[-2])
    return float(closes.iloc[-1])


def get_tape_quotes(symbols: list[str]) -> dict[str, dict]:
    """Return {symbol: {price, change, change_pct}} for the given symbols.

    Symbols that fail to resolve are simply omitted (the caller keeps their
    label and renders a placeholder price).
    """
    out: dict[str, dict] = {}
    if not symbols:
        return out

    daily = _safe_download(symbols, period="5d", interval="1d", prepost=False)
    intraday = _safe_download(symbols, period="1d", interval="1m", prepost=True)

    for sym in symbols:
        closes = _series_for(daily, sym, "Close")
        if closes is None or closes.empty:
            continue

        prev_close = _prev_close(closes)
        price = float(closes.iloc[-1])

        # Prefer a live intraday quote (incl. pre/post-market) when available.
        intr = _series_for(intraday, sym, "Close")
        if intr is not None and not intr.empty:
            price = float(intr.iloc[-1])

        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        out[sym] = {
            "price": round(price, 4),
            "change": round(change, 4),
            "change_pct": round(change_pct, 2),
        }

    logger.debug(f"Tape: resolved {len(out)}/{len(symbols)} symbols")
    return out
