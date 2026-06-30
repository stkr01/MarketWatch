"""Top N tickers universe for scanning"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Top 10 tickers for initial development
# These are highly liquid with frequent news coverage
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
    "MSTR"    # MicroStrategy
]


def get_ticker_universe() -> list[str]:
    """Get the list of tickers to scan based on configuration"""
    universe = TOP_TICKERS[:settings.TOP_N_TICKERS]
    logger.info(f"Ticker universe: {len(universe)} tickers")
    return universe


def get_ticker_info(ticker: str) -> dict:
    """Basic ticker info (can be enhanced with metadata API later)"""
    return {
        "symbol": ticker,
        "exchange": "NASDAQ" if ticker in ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "NFLX", "AMD"] else "NYSE",
        "name": ticker,  # Could fetch from yfinance
    }
