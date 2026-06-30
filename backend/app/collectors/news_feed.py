"""Collect news from major financial sources"""
import feedparser
from datetime import datetime, timedelta
from app.config import settings

# RSS feed URLs for major financial news sources
NEWS_FEEDS = {
    "MarketWatch": "https://feeds.bloomberg.com/markets/news.rss",
    "CNBC": "https://feeds.cnbc.com/id/100003114/",
    "Yahoo Finance": "https://feeds.finance.yahoo.com/rss/2.0/headline",
    "Google News": "https://news.google.com/rss/search?q=stock",
}


def get_news_for_ticker(ticker: str) -> list[dict]:
    """Get recent news items for a ticker"""
    news_items = []
    lookback_hours = settings.NEWS_LOOKBACK_HOURS

    for source_name, feed_url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:10]:  # Get latest 10 from each source
                # Check if ticker appears in title or summary
                title = entry.get("title", "")
                summary = entry.get("summary", "")

                if ticker.upper() in title.upper() or ticker.upper() in summary.upper():
                    published = entry.get("published_parsed")
                    published_dt = datetime(*published[:6]) if published else datetime.utcnow()

                    # Filter by lookback period
                    if (datetime.utcnow() - published_dt).total_seconds() <= lookback_hours * 3600:
                        news_items.append({
                            "ticker": ticker,
                            "title": title,
                            "source": source_name,
                            "url": entry.get("link", ""),
                            "published_at": published_dt,
                            "summary": summary[:200] if summary else None
                        })

        except Exception as e:
            print(f"Error fetching news from {source_name}: {e}")

    return sorted(news_items, key=lambda x: x["published_at"], reverse=True)


def get_bulk_news(tickers: list[str]) -> dict:
    """Get news for multiple tickers"""
    results = {}
    for ticker in tickers:
        results[ticker] = get_news_for_ticker(ticker)
    return results
