"""Collect news from major financial sources"""
import feedparser
from datetime import datetime, timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# RSS feed URLs for major financial news sources
NEWS_FEEDS = {
    "CNBC": "https://feeds.cnbc.com/id/100003114/",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Yahoo Finance": "https://feeds.finance.yahoo.com/rss/2.0/headline",
}


def get_news_for_ticker(ticker: str) -> list[dict]:
    """
    Get recent news items for a ticker from RSS feeds

    Searches news feeds for ticker mentions in title/summary
    Filters by recency (lookback_hours from config)
    """
    news_items = []
    lookback_hours = settings.NEWS_LOOKBACK_HOURS
    lookback_seconds = lookback_hours * 3600

    ticker_upper = ticker.upper()

    for source_name, feed_url in NEWS_FEEDS.items():
        try:
            logger.debug(f"Fetching news from {source_name} for {ticker}")
            feed = feedparser.parse(feed_url)

            if not feed.entries:
                logger.debug(f"No entries from {source_name}")
                continue

            for entry in feed.entries[:20]:  # Check up to 20 entries per source
                title = entry.get("title", "").upper()
                summary = entry.get("summary", "").upper()
                link = entry.get("link", "")

                # Check if ticker appears in title or summary
                if ticker_upper not in title and ticker_upper not in summary:
                    continue

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
                    "source": source_name,
                    "url": link,
                    "published_at": published_dt,
                    "summary": entry.get("summary", "")[:300] if entry.get("summary") else None
                })

        except Exception as e:
            logger.warning(f"Error fetching news from {source_name}: {str(e)}")

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
