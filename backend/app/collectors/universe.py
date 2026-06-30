"""Top N tickers universe for scanning"""
from app.config import settings

# Top 10 tickers for initial development
# These are the most liquid and have the most news coverage
TOP_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "AMZN",
    "META",
    "GOOGL",
    "NFLX",
    "AMD",
    "MSTR"
]


def get_ticker_universe() -> list[str]:
    """Get the list of tickers to scan"""
    return TOP_TICKERS[:settings.TOP_N_TICKERS]
