"""Intraday price series for the detail chart and the candidate-table sparklines.

Two shapes:
- get_history(symbol)   → full intraday 1m series (incl pre/post) + prior close,
                          for the line chart in the stock-detail panel.
- get_sparklines(syms)  → one batched download, downsampled to a handful of
                          points per symbol, for the tiny table sparklines.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")


def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _series_for(frame: pd.DataFrame | None, symbol: str, field: str = "Close") -> pd.Series | None:
    """Extract one field's Series for `symbol` from a (possibly grouped) frame."""
    if frame is None or frame.empty:
        return None
    cols = frame.columns
    try:
        if isinstance(cols, pd.MultiIndex):
            if symbol in cols.get_level_values(0):
                s = frame[symbol][field]
            elif symbol in cols.get_level_values(1):
                s = frame[field][symbol]
            else:
                return None
        else:
            s = frame[field]
    except (KeyError, IndexError):
        return None
    return s.dropna()


def _downsample(values: list[float], target: int) -> list[float]:
    """Evenly thin `values` down to at most `target` points (keeping the last)."""
    n = len(values)
    if n <= target:
        return [round(v, 4) for v in values]
    step = n / target
    out = [values[min(int(i * step), n - 1)] for i in range(target)]
    out[-1] = values[-1]              # always keep the latest price
    return [round(v, 4) for v in out]


def _prev_close(symbol: str) -> float | None:
    """Most recent completed daily close before today (Eastern)."""
    try:
        daily = yf.download(symbol, period="7d", interval="1d",
                            progress=False, threads=False)
    except Exception as e:
        logger.warning(f"prev_close fetch failed for {symbol}: {e}")
        return None
    if daily is None or daily.empty:
        return None
    daily = _flatten(daily)
    closes = daily["Close"].dropna()
    if closes.empty:
        return None
    today = datetime.now(ET).date()
    prior = [float(c) for idx, c in zip(closes.index, closes)
             if getattr(idx, "date", lambda: None)() and idx.date() < today]
    if prior:
        return round(prior[-1], 4)
    return round(float(closes.iloc[-1]), 4)


def get_history(symbol: str) -> dict:
    """Intraday 1-minute closes (incl. pre/post-market) for one ticker."""
    points: list[dict] = []
    try:
        intr = yf.download(symbol, period="1d", interval="1m",
                           prepost=True, progress=False, threads=False)
    except Exception as e:
        logger.warning(f"History fetch failed for {symbol}: {e}")
        intr = None

    if intr is not None and not intr.empty:
        intr = _flatten(intr)
        close = intr["Close"].dropna()
        for ts, val in close.items():
            try:
                iso = ts.tz_convert(ET).isoformat() if ts.tzinfo else ts.isoformat()
            except Exception:
                iso = str(ts)
            points.append({"t": iso, "price": round(float(val), 4)})

    return {"symbol": symbol, "points": points, "prev_close": _prev_close(symbol)}


def get_sparklines(symbols: list[str], points: int = 40) -> dict[str, list[float]]:
    """Downsampled intraday series for many symbols in one batched fetch."""
    out: dict[str, list[float]] = {}
    if not symbols:
        return out
    try:
        df = yf.download(symbols, period="1d", interval="5m", prepost=True,
                         group_by="ticker", progress=False, threads=True)
    except Exception as e:
        logger.warning(f"Sparkline fetch failed: {e}")
        return out

    for sym in symbols:
        s = _series_for(df, sym, "Close")
        if s is None or s.empty:
            continue
        out[sym] = _downsample([float(x) for x in s.tolist()], points)
    return out
