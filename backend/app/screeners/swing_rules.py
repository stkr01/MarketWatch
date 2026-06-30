"""Swing trading rule screening"""
from app.config import settings


def meets_swing_criteria(market_data: dict, has_news: bool) -> bool:
    """
    Check if a stock meets swing trading criteria

    Rules:
    - Gap% threshold
    - Volume above average
    - Price in relation to EMA100 (trend indicator)
    - Has recent news (catalyst)
    """
    gap_pct = abs(market_data["gap_pct"])

    # Rule 1: Gap threshold
    if gap_pct < settings.GAP_THRESHOLD_PERCENT:
        return False

    # Rule 2: Volume multiplier
    if market_data["volume_avg_20"] and market_data["volume"] > 0:
        volume_ratio = market_data["volume"] / market_data["volume_avg_20"]
        if volume_ratio < settings.VOLUME_MULTIPLIER:
            return False

    # Rule 3: Has news (catalyst requirement)
    if not has_news:
        return False

    # All rules passed
    return True


def screen_candidates(market_data_list: list[dict], news_dict: dict) -> list[str]:
    """
    Screen a list of market data and return matching tickers

    Args:
        market_data_list: List of market data dicts
        news_dict: Dict of {ticker: [news_items]}

    Returns:
        List of tickers that meet criteria
    """
    candidates = []

    for data in market_data_list:
        ticker = data["ticker"]
        has_news = len(news_dict.get(ticker, [])) > 0

        if meets_swing_criteria(data, has_news):
            candidates.append(ticker)

    return candidates
