"""Collect market data using yfinance"""
import yfinance as yf
import pandas as pd
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
import logging
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# US equities trade on Eastern Time; pre-market 04:00–09:30, regular 09:30–16:00,
# post-market 16:00–20:00.
ET = ZoneInfo("America/New_York")


def _to_float(value) -> float:
    """Robustly coerce a pandas/numpy scalar to a Python float."""
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def _compute_rsi(close: pd.Series, period: int = 14) -> float | None:
    """Wilder's RSI on closing prices."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    last_gain = avg_gain.iloc[-1]
    last_loss = avg_loss.iloc[-1]
    if pd.isna(last_gain) or pd.isna(last_loss):
        return None
    if last_loss == 0:
        return 100.0
    rs = _to_float(last_gain) / _to_float(last_loss)
    return round(100 - (100 / (1 + rs)), 2)


def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float | None:
    """Wilder's Average True Range."""
    prev_close = close.shift(1)
    true_range = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    last = atr.iloc[-1]
    if pd.isna(last):
        return None
    return round(_to_float(last), 2)


def _classify_session(ts_et) -> str:
    """Map an Eastern-time timestamp to a trading session label."""
    t = ts_et.time()
    if dtime(4, 0) <= t < dtime(9, 30):
        return "premarket"
    if dtime(9, 30) <= t < dtime(16, 0):
        return "regular"
    if dtime(16, 0) <= t < dtime(20, 0):
        return "postmarket"
    return "closed"


def _get_intraday_snapshot(ticker: str) -> dict | None:
    """
    Latest intraday price including pre/post-market, from 1-minute bars.

    This is what makes the gap reflect *real* pre-market movement (the last
    actual trade before the open) instead of yesterday's daily open.
    """
    try:
        intraday = yf.download(
            ticker, period="2d", interval="1m",
            prepost=True, progress=False, threads=False,
        )
    except Exception as e:
        logger.warning(f"Intraday fetch failed for {ticker}: {e}")
        return None

    if intraday is None or intraday.empty:
        return None

    if isinstance(intraday.columns, pd.MultiIndex):
        intraday.columns = intraday.columns.get_level_values(0)

    close = intraday["Close"].dropna()
    if close.empty:
        return None

    last_ts = close.index[-1]
    try:
        if last_ts.tzinfo is None:
            ts_et = last_ts.tz_localize("UTC").tz_convert(ET)
        else:
            ts_et = last_ts.tz_convert(ET)
    except Exception:
        ts_et = last_ts

    return {
        "price": _to_float(close.iloc[-1]),
        "session": _classify_session(ts_et),
        "as_of": ts_et,
    }


def _previous_regular_close(daily: pd.DataFrame) -> float | None:
    """
    Most recent completed regular-session close *before* today (Eastern).

    Using the prior day's close as the gap reference means the gap is measured
    the same way whether we run in pre-market, regular hours, or post-market.
    """
    today_et = datetime.now(ET).date()
    closes = daily["Close"]
    prior = [c for idx, c in zip(daily.index, closes) if idx.date() < today_et]
    if prior:
        return _to_float(prior[-1])
    # Fallbacks: prefer the second-to-last daily bar, else the last one.
    if len(closes) >= 2:
        return _to_float(closes.iloc[-2])
    if len(closes) >= 1:
        return _to_float(closes.iloc[-1])
    return None


def get_market_data(ticker: str) -> dict | None:
    """
    Get gap%, volume, EMA100 for a ticker

    Returns dict with market data or None if fetch fails
    """
    try:
        # Download 1 year of history so the 100-day EMA has enough data to
        # be meaningful (a 3-month window only has ~63 trading days < 100).
        data = yf.download(ticker, period="1y", progress=False, threads=False)

        if data is None or data.empty or len(data) < 2:
            logger.warning(f"Insufficient data for {ticker}")
            return None

        # Flatten columns if MultiIndex (yfinance can return MultiIndex for single ticker)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Most recent daily bar (used for volume + as a price fallback).
        current_row = data.iloc[-1]
        daily_close = _to_float(current_row['Close'])
        current_volume = _to_float(current_row['Volume'])

        # Reference close for the gap = prior completed regular-session close.
        previous_close = _previous_regular_close(data)
        if previous_close is None or previous_close <= 0:
            previous_close = daily_close

        # Live price: prefer a real intraday (incl. pre/post-market) quote so the
        # gap reflects actual pre-market movement, not yesterday's daily open.
        live_price = daily_close
        price_source = "daily"
        pre_market_price = None
        if settings.USE_PREMARKET_DATA:
            snapshot = _get_intraday_snapshot(ticker)
            if snapshot and snapshot["price"] > 0:
                live_price = snapshot["price"]
                price_source = snapshot["session"]  # premarket / regular / postmarket / closed
                pre_market_price = snapshot["price"]

        # Calculate gap percentage (live price vs. prior regular close)
        gap_pct = 0.0
        if previous_close > 0:
            gap_pct = ((live_price - previous_close) / previous_close) * 100

        # Calculate 20-day average volume
        volume_mean = data['Volume'].tail(20).mean()
        volume_avg_20 = float(volume_mean.item() if hasattr(volume_mean, 'item') else volume_mean)

        if np.isnan(volume_avg_20) or volume_avg_20 <= 0:
            volume_avg_20 = current_volume

        # Calculate EMA100
        ema_100_series = data['Close'].ewm(span=100).mean()
        ema_100_val = ema_100_series.iloc[-1]
        ema_100 = float(ema_100_val.item() if hasattr(ema_100_val, 'item') else ema_100_val)
        above_ema = live_price > ema_100

        # Additional swing indicators
        rvol = round(current_volume / volume_avg_20, 2) if volume_avg_20 > 0 else None
        rsi_14 = _compute_rsi(data['Close'])
        atr_14 = _compute_atr(data['High'], data['Low'], data['Close'])
        atr_pct = round((atr_14 / live_price) * 100, 2) if atr_14 and live_price > 0 else None

        result = {
            "ticker": ticker,
            "gap_pct": float(gap_pct),
            "volume": current_volume,
            "volume_avg_20": volume_avg_20,
            "rvol": rvol,
            "price": live_price,
            "previous_close": float(previous_close),
            "pre_market_price": pre_market_price,
            "price_source": price_source,
            "ema_100": ema_100,
            "above_ema_100": bool(above_ema),
            "rsi_14": rsi_14,
            "atr_14": atr_14,
            "atr_pct": atr_pct,
            "timestamp": datetime.utcnow()
        }

        logger.debug(
            f"{ticker}: gap={gap_pct:.2f}%, price=${live_price:.2f} ({price_source}), "
            f"prev_close=${previous_close:.2f}, RVOL={rvol}, RSI={rsi_14}, ATR%={atr_pct}"
        )
        return result

    except Exception as e:
        logger.error(f"Error fetching market data for {ticker}: {str(e)}")
        return None


def get_bulk_market_data(tickers: list[str]) -> list[dict]:
    """Get market data for multiple tickers"""
    results = []
    logger.info(f"Fetching market data for {len(tickers)} tickers")

    for ticker in tickers:
        data = get_market_data(ticker)
        if data:
            results.append(data)
        else:
            logger.warning(f"Skipped {ticker} - no data")

    logger.info(f"Successfully fetched {len(results)}/{len(tickers)} tickers")
    return results
