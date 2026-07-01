"""Collect market data using yfinance"""
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


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

        # Get most recent row values as numpy arrays then extract scalar
        current_row = data.iloc[-1]
        prev_row = data.iloc[-2]

        # Convert Series values to scalars using .item() or direct access
        current_open = float(current_row['Open'].item() if hasattr(current_row['Open'], 'item') else current_row['Open'])
        current_close = float(current_row['Close'].item() if hasattr(current_row['Close'], 'item') else current_row['Close'])
        current_volume = float(current_row['Volume'].item() if hasattr(current_row['Volume'], 'item') else current_row['Volume'])
        previous_close = float(prev_row['Close'].item() if hasattr(prev_row['Close'], 'item') else prev_row['Close'])

        # Calculate gap percentage
        gap_pct = 0.0
        if previous_close > 0:
            gap_pct = ((current_open - previous_close) / previous_close) * 100

        # Calculate 20-day average volume
        volume_mean = data['Volume'].tail(20).mean()
        volume_avg_20 = float(volume_mean.item() if hasattr(volume_mean, 'item') else volume_mean)

        if np.isnan(volume_avg_20) or volume_avg_20 <= 0:
            volume_avg_20 = current_volume

        # Calculate EMA100
        ema_100_series = data['Close'].ewm(span=100).mean()
        ema_100_val = ema_100_series.iloc[-1]
        ema_100 = float(ema_100_val.item() if hasattr(ema_100_val, 'item') else ema_100_val)
        above_ema = current_close > ema_100

        # Additional swing indicators
        rvol = round(current_volume / volume_avg_20, 2) if volume_avg_20 > 0 else None
        rsi_14 = _compute_rsi(data['Close'])
        atr_14 = _compute_atr(data['High'], data['Low'], data['Close'])
        atr_pct = round((atr_14 / current_close) * 100, 2) if atr_14 and current_close > 0 else None

        result = {
            "ticker": ticker,
            "gap_pct": float(gap_pct),
            "volume": current_volume,
            "volume_avg_20": volume_avg_20,
            "rvol": rvol,
            "price": current_close,
            "ema_100": ema_100,
            "above_ema_100": bool(above_ema),
            "rsi_14": rsi_14,
            "atr_14": atr_14,
            "atr_pct": atr_pct,
            "timestamp": datetime.utcnow()
        }

        logger.debug(
            f"{ticker}: gap={gap_pct:.2f}%, price=${current_close:.2f}, "
            f"RVOL={rvol}, RSI={rsi_14}, ATR%={atr_pct}"
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
