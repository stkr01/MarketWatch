"""Collect market data using yfinance"""
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

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

        current = data.iloc[-1]
        previous = data.iloc[-2]

        # Calculate gap percentage
        gap_pct = 0.0
        if previous['Close'] > 0:
            gap_pct = ((current['Open'] - previous['Close']) / previous['Close']) * 100

        # Calculate 20-day average volume
        volume_avg_20 = data['Volume'].tail(20).mean()
        if pd.isna(volume_avg_20) or volume_avg_20 == 0:
            volume_avg_20 = current['Volume']

        # Calculate EMA100
        ema_100 = data['Close'].ewm(span=100).mean().iloc[-1]
        above_ema = float(current['Close']) > float(ema_100)

        result = {
            "ticker": ticker,
            "gap_pct": float(gap_pct),
            "volume": float(current['Volume']),
            "volume_avg_20": float(volume_avg_20),
            "price": float(current['Close']),
            "ema_100": float(ema_100),
            "above_ema_100": bool(above_ema),
            "timestamp": datetime.utcnow()
        }

        logger.debug(f"{ticker}: gap={gap_pct:.2f}%, price=${current['Close']:.2f}, EMA100=${ema_100:.2f}")
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
