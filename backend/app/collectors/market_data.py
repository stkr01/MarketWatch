"""Collect market data using yfinance"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from app.config import settings


def get_market_data(ticker: str) -> dict:
    """Get gap%, volume, EMA100 for a ticker"""
    try:
        data = yf.download(ticker, period="3mo", progress=False)

        if data.empty:
            return None

        current = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else None

        gap_pct = 0
        if previous is not None and previous['Close'] > 0:
            gap_pct = ((current['Open'] - previous['Close']) / previous['Close']) * 100

        volume_avg_20 = data['Volume'].tail(20).mean()

        ema_100 = data['Close'].ewm(span=100).mean().iloc[-1]
        above_ema = current['Close'] > ema_100

        return {
            "ticker": ticker,
            "gap_pct": gap_pct,
            "volume": current['Volume'],
            "volume_avg_20": volume_avg_20,
            "price": current['Close'],
            "ema_100": ema_100,
            "above_ema_100": above_ema,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def get_bulk_market_data(tickers: list[str]) -> list[dict]:
    """Get market data for multiple tickers"""
    results = []
    for ticker in tickers:
        data = get_market_data(ticker)
        if data:
            results.append(data)
    return results
