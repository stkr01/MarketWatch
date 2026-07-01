"""Collect news from major financial sources"""
import feedparser
from datetime import datetime
from urllib.parse import quote
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Yahoo Finance exposes a per-ticker RSS feed. Every entry in this feed is
# already about the requested symbol, so no fragile substring matching is
# needed (the old approach matched "META" inside "metal", missed most real
# news, and scanned generic top-stories feeds that rarely name a ticker).
YAHOO_TICKER_FEED = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline"
    "?s={symbol}&region=US&lang=en-US"
)


def get_news_for_ticker(ticker: str) -> list[dict]:
    """
    Get recent news items for a ticker from Yahoo Finance's per-ticker RSS feed.

    Filters by recency (lookback_hours from config).
    """
    news_items = []
    lookback_hours = settings.NEWS_LOOKBACK_HOURS
    lookback_seconds = lookback_hours * 3600

    feed_url = YAHOO_TICKER_FEED.format(symbol=quote(ticker.upper()))

    try:
        logger.debug(f"Fetching Yahoo Finance news for {ticker}")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            link = entry.get("link", "")

            # Parse publication date
            try:
                if entry.get("published_parsed"):
                    published_dt = datetime(*entry["published_parsed"][:6])
                else:
                    published_dt = datetime.utcnow()
            except (TypeError, ValueError):
                published_dt = datetime.utcnow()

            # Filter by lookback period
            age_seconds = (datetime.utcnow() - published_dt).total_seconds()
            if age_seconds > lookback_seconds:
                continue

            news_items.append({
                "ticker": ticker,
                "title": entry.get("title", ""),
                "source": "Yahoo Finance",
                "url": link,
                "published_at": published_dt,
                "summary": entry.get("summary", "")[:300] if entry.get("summary") else None
            })

    except Exception as e:
        logger.warning(f"Error fetching Yahoo Finance news for {ticker}: {str(e)}")

    # Sort by recency
    result = sorted(news_items, key=lambda x: x["published_at"], reverse=True)
    logger.info(f"{ticker}: Found {len(result)} news items in last {lookback_hours}h")
    return result


def get_bulk_news(tickers: list[str]) -> dict:
    """Get news for multiple tickers"""
    logger.info(f"Fetching news for {len(tickers)} tickers")
    results = {}

    for ticker in tickers:
        results[ticker] = get_news_for_ticker(ticker)

    total_news = sum(len(items) for items in results.values())
    logger.info(f"Total news items collected: {total_news}")

    return results
