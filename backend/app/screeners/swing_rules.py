"""Swing trading rule screening logic"""
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def meets_swing_criteria(market_data: dict, has_news: bool) -> tuple[bool, dict]:
    """
    Check if a stock meets swing trading criteria

    Rules:
    1. Gap% threshold (±2% default)
    2. Volume above average (1.5x 20-day avg default)
    3. Price in relation to EMA100 (trend indicator - info only, not hard filter)
    4. Has recent news (catalyst - required)

    Returns:
        (meets_criteria: bool, details: dict with rule scores)
    """
    details = {
        "ticker": market_data.get("ticker"),
        "gap_pct": market_data["gap_pct"],
        "volume_ratio": 0.0,
        "has_news": has_news,
        "above_ema_100": market_data.get("above_ema_100"),
        "fail_reason": None
    }

    gap_pct = abs(market_data["gap_pct"])

    # Rule 1: Gap threshold
    if gap_pct < settings.GAP_THRESHOLD_PERCENT:
        details["fail_reason"] = f"Gap {gap_pct:.2f}% < threshold {settings.GAP_THRESHOLD_PERCENT}%"
        return False, details

    # Rule 2: Volume multiplier
    volume_avg = market_data.get("volume_avg_20", 1)
    volume = market_data.get("volume", 0)

    if volume > 0 and volume_avg > 0:
        volume_ratio = volume / volume_avg
        details["volume_ratio"] = volume_ratio

        if volume_ratio < settings.VOLUME_MULTIPLIER:
            details["fail_reason"] = f"Volume ratio {volume_ratio:.2f}x < threshold {settings.VOLUME_MULTIPLIER}x"
            return False, details
    else:
        details["fail_reason"] = "Invalid volume data"
        return False, details

    # Rule 3: News/catalyst requirement
    if not has_news:
        details["fail_reason"] = "No recent news (catalyst)"
        return False, details

    # All rules passed
    return True, details


def screen_candidates(market_data_list: list[dict], news_dict: dict) -> dict:
    """
    Screen a list of market data and return matching tickers with details

    Args:
        market_data_list: List of market data dicts
        news_dict: Dict of {ticker: [news_items]}

    Returns:
        {
            "candidates": [ticker_str],
            "details": {ticker_str: {rule_details}},
            "summary": "X/Y candidates matched"
        }
    """
    candidates = []
    details_map = {}

    logger.info(f"Screening {len(market_data_list)} tickers")

    for data in market_data_list:
        ticker = data["ticker"]
        has_news = len(news_dict.get(ticker, [])) > 0

        meets_criteria, rule_details = meets_swing_criteria(data, has_news)

        if meets_criteria:
            candidates.append(ticker)
            logger.info(f"✓ {ticker}: CANDIDATE (gap={data['gap_pct']:.2f}%, vol={rule_details['volume_ratio']:.2f}x, news={has_news})")
        else:
            logger.debug(f"✗ {ticker}: {rule_details['fail_reason']}")

        details_map[ticker] = rule_details

    result = {
        "candidates": candidates,
        "details": details_map,
        "summary": f"{len(candidates)}/{len(market_data_list)} candidates matched"
    }

    logger.info(f"Screening complete: {result['summary']}")
    return result
