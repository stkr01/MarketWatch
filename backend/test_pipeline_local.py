#!/usr/bin/env python
"""
Local test script for the market scanning pipeline

Run this to verify data collection, screening, and database writes
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_imports():
    """Verify all imports work"""
    logger.info("Testing imports...")
    try:
        from app.config import settings
        from app.collectors.universe import get_ticker_universe
        from app.collectors.market_data import get_bulk_market_data
        from app.collectors.news_feed import get_bulk_news
        from app.screeners.swing_rules import screen_candidates
        from app.pipeline import run_market_scan
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_config():
    """Verify configuration"""
    logger.info("\nTesting configuration...")
    try:
        from app.config import settings
        logger.info(f"  Environment: {settings.ENVIRONMENT}")
        logger.info(f"  Debug: {settings.DEBUG}")
        logger.info(f"  Top N Tickers: {settings.TOP_N_TICKERS}")
        logger.info(f"  Gap Threshold: {settings.GAP_THRESHOLD_PERCENT}%")
        logger.info(f"  Volume Multiplier: {settings.VOLUME_MULTIPLIER}x")
        logger.info(f"  News Lookback: {settings.NEWS_LOOKBACK_HOURS}h")
        logger.info(f"  API Key configured: {'✓' if settings.ANTHROPIC_API_KEY else '✗'}")
        logger.info("✓ Configuration loaded")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration failed: {e}")
        return False


def test_database():
    """Verify database setup"""
    logger.info("\nTesting database...")
    try:
        from app.db import Base, engine, ensure_schema
        from app.models import Ticker, Scan, ScanResult, NewsItem, AIAnalysis

        # Create tables and apply lightweight migrations (mirrors app startup)
        Base.metadata.create_all(bind=engine)
        ensure_schema()
        logger.info(f"  Database URL: {engine.url}")
        logger.info("✓ Database tables created")
        return True
    except Exception as e:
        logger.error(f"✗ Database failed: {e}")
        return False


def test_collectors():
    """Test data collectors"""
    logger.info("\nTesting collectors...")
    try:
        from app.collectors.universe import get_ticker_universe
        from app.collectors.market_data import get_bulk_market_data
        from app.collectors.news_feed import get_bulk_news

        # Get universe
        tickers = get_ticker_universe()
        logger.info(f"  ✓ Universe: {len(tickers)} tickers")

        if len(tickers) == 0:
            logger.error("✗ No tickers loaded")
            return False

        # Test market data (limit to first 2 for speed)
        logger.info("  Fetching market data (first 2 tickers)...")
        market_data = get_bulk_market_data(tickers[:2])
        logger.info(f"  ✓ Market data: {len(market_data)}/2 tickers")

        if market_data:
            sample = market_data[0]
            logger.info(f"    Sample: {sample['ticker']} gap={sample['gap_pct']:.2f}% price=${sample['price']:.2f}")

        # Test news (limit to first 2)
        logger.info("  Fetching news (first 2 tickers)...")
        news = get_bulk_news(tickers[:2])
        total_news = sum(len(items) for items in news.values())
        logger.info(f"  ✓ News: {total_news} items found")

        logger.info("✓ Collectors working")
        return True

    except Exception as e:
        logger.error(f"✗ Collectors failed: {e}", exc_info=True)
        return False


def test_screener():
    """Test screening logic"""
    logger.info("\nTesting screener...")
    try:
        from app.screeners.swing_rules import screen_candidates
        from datetime import datetime

        # Mock market data
        market_data = [
            {
                "ticker": "TEST1",
                "gap_pct": 3.5,
                "volume": 5000000,
                "volume_avg_20": 2000000,
                "price": 150.0,
                "ema_100": 145.0,
                "above_ema_100": True,
                "timestamp": datetime.utcnow()
            },
            {
                "ticker": "TEST2",
                "gap_pct": 0.5,  # Too small gap
                "volume": 3000000,
                "volume_avg_20": 2000000,
                "price": 100.0,
                "ema_100": 98.0,
                "above_ema_100": True,
                "timestamp": datetime.utcnow()
            }
        ]

        news_dict = {
            "TEST1": [{"title": "News for TEST1"}],  # Has news
            "TEST2": []  # No news
        }

        result = screen_candidates(market_data, news_dict)
        candidates = result["candidates"]
        logger.info(f"  Screened {len(market_data)} stocks → {len(candidates)} candidates")
        logger.info(f"  Candidates: {candidates}")
        logger.info("✓ Screener working")
        return True

    except Exception as e:
        logger.error(f"✗ Screener failed: {e}", exc_info=True)
        return False


def test_full_pipeline():
    """Run full pipeline"""
    logger.info("\nTesting full pipeline...")
    try:
        from app.pipeline import run_market_scan
        result = run_market_scan()
        logger.info(f"  Scan ID: {result['scan_id']}")
        logger.info(f"  Candidates: {result['candidates']}")
        logger.info(f"  Summary: {result['summary']}")
        logger.info(f"  Duration: {result['duration_seconds']:.1f}s")
        logger.info("✓ Pipeline complete")
        return True
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}", exc_info=True)
        return False


def test_claude_api():
    """Test Claude API integration"""
    logger.info("\nTesting Claude API...")
    try:
        from app.config import settings

        if not settings.ANTHROPIC_API_KEY:
            logger.warning("⚠ Claude API key not configured - skipping")
            return True

        from app.ai.claude_analyzer import analyze_stock_candidate
        from datetime import datetime

        # Mock data
        market_data = {
            "gap_pct": 2.5,
            "volume": 5000000,
            "volume_avg_20": 2000000,
            "price": 150.0,
            "ema_100": 145.0,
            "above_ema_100": True
        }

        news = [
            {
                "title": "Company announces earnings beat",
                "source": "CNBC",
                "published_at": datetime.utcnow()
            }
        ]

        logger.info("  Sending test request to Claude API...")
        result = analyze_stock_candidate("TEST", market_data, news)
        logger.info(f"  ✓ Response received ({result['usage_tokens']} tokens)")
        logger.info(f"  Analysis: {result['response'][:100]}...")
        logger.info("✓ Claude API working")
        return True

    except Exception as e:
        logger.error(f"✗ Claude API failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("PRE-MARKET DASHBOARD - PIPELINE TEST")
    logger.info("="*60)

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Collectors", test_collectors),
        ("Screener", test_screener),
        ("Full Pipeline", test_full_pipeline),
        ("Claude API", test_claude_api),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info("="*60)
    logger.info(f"Result: {passed_count}/{total_count} tests passed")
    logger.info("="*60)

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
