"""End-to-end market scan pipeline"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Ticker, Scan, ScanResult, NewsItem
from app.collectors.universe import get_ticker_universe
from app.collectors.market_data import get_bulk_market_data
from app.collectors.news_feed import get_bulk_news
from app.screeners.swing_rules import screen_candidates
from app.outcomes import record_candidate_outcomes
from app.config import settings

logger = logging.getLogger(__name__)


def run_market_scan() -> dict:
    """
    Execute a complete market scan pipeline

    1. Get ticker universe
    2. Fetch market data (yfinance)
    3. Fetch news (feedparser)
    4. Screen against swing trading rules
    5. Save results to database

    Returns:
        {
            "scan_id": int,
            "candidates": [str],
            "summary": str
        }
    """
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        logger.info("="*60)
        logger.info("Starting market scan pipeline")
        logger.info("="*60)

        # Step 1: Get ticker universe
        tickers = get_ticker_universe()
        logger.info(f"Step 1: Universe loaded - {len(tickers)} tickers")

        # Step 2: Fetch market data
        logger.info("Step 2: Fetching market data...")
        market_data_list = get_bulk_market_data(tickers)
        logger.info(f"  → {len(market_data_list)} tickers fetched successfully")

        # Step 3: Fetch news
        logger.info("Step 3: Fetching news...")
        news_dict = get_bulk_news(tickers)
        logger.info(f"  → News fetched for {len(news_dict)} tickers")

        # Step 4: Screen candidates
        logger.info("Step 4: Screening against swing trading rules...")
        screening_result = screen_candidates(market_data_list, news_dict)
        candidates = screening_result["candidates"]
        details_map = screening_result["details"]
        logger.info(f"  → {screening_result['summary']}")

        # Step 5: Save to database
        logger.info("Step 5: Saving results to database...")

        # Create or update tickers
        for ticker in tickers:
            existing = db.query(Ticker).filter(Ticker.symbol == ticker).first()
            if not existing:
                new_ticker = Ticker(symbol=ticker, name=ticker, exchange="NASDAQ")
                db.add(new_ticker)
        db.commit()

        # Create scan record
        scan = Scan(
            timestamp=start_time,
            status="completed",
            candidate_count=len(candidates)
        )
        db.add(scan)
        db.flush()  # Get scan ID

        # Save scan results
        candidate_set = set(candidates)
        for data in market_data_list:
            ticker_obj = db.query(Ticker).filter(Ticker.symbol == data["ticker"]).first()
            if ticker_obj:
                has_news = len(news_dict.get(data["ticker"], [])) > 0

                scan_result = ScanResult(
                    scan_id=scan.id,
                    ticker_id=ticker_obj.id,
                    gap_pct=data["gap_pct"],
                    volume=data["volume"],
                    volume_avg_20=data["volume_avg_20"],
                    rvol=data.get("rvol"),
                    price=data["price"],
                    ema_100=data["ema_100"],
                    above_ema_100=data["above_ema_100"],
                    rsi_14=data.get("rsi_14"),
                    atr_14=data.get("atr_14"),
                    atr_pct=data.get("atr_pct"),
                    has_news=has_news,
                    is_candidate=data["ticker"] in candidate_set,
                    timestamp=data["timestamp"]
                )
                db.add(scan_result)

        # Save news items
        for ticker, news_items in news_dict.items():
            ticker_obj = db.query(Ticker).filter(Ticker.symbol == ticker).first()
            if ticker_obj and news_items:
                for news in news_items:
                    # Check if news already exists (avoid duplicates)
                    existing = db.query(NewsItem).filter(
                        NewsItem.ticker_id == ticker_obj.id,
                        NewsItem.url == news["url"]
                    ).first()

                    if not existing:
                        news_item = NewsItem(
                            ticker_id=ticker_obj.id,
                            title=news["title"],
                            source=news["source"],
                            url=news["url"],
                            published_at=news["published_at"]
                        )
                        db.add(news_item)

        db.commit()
        logger.info(f"  → Scan {scan.id} saved to database")

        # Track candidate outcomes (dedup per day) for performance analytics
        candidate_data = [d for d in market_data_list if d["ticker"] in candidate_set]
        record_candidate_outcomes(db, scan.id, candidate_data)

        # Summary
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info("="*60)
        logger.info(f"Scan complete in {elapsed:.1f}s")
        logger.info(f"Candidates: {len(candidates)}")
        logger.info(f"Candidates: {', '.join(candidates) if candidates else 'None'}")
        logger.info("="*60)

        return {
            "scan_id": scan.id,
            "candidates": candidates,
            "summary": screening_result["summary"],
            "duration_seconds": elapsed
        }

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        db.rollback()
        raise

    finally:
        db.close()
