"""Collect market data using yfinance"""
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


def get_market_data(ticker: str) -> dict | None:
    """
    Get gap%, volume, EMA100 for a ticker

    Returns dict with market data or None if fetch fails
    """
    try:
        # Download 3 months of historical data for EMA calculation
        data = yf.download(ticker, period="3mo", progress=False, threads=False)

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

        result = {
            "ticker": ticker,
            "gap_pct": float(gap_pct),
            "volume": current_volume,
            "volume_avg_20": volume_avg_20,
            "price": current_close,
            "ema_100": ema_100,
            "above_ema_100": bool(above_ema),
            "timestamp": datetime.utcnow()
        }

        logger.debug(f"{ticker}: gap={gap_pct:.2f}%, price=${current_close:.2f}, EMA100=${ema_100:.2f}")
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
