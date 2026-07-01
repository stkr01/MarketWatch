"""Collect the US economic calendar for the current day.

Data source: faireconomy.media weekly JSON mirror of the ForexFactory
calendar. It's free, needs no API key, and includes country, event title,
scheduled datetime (with US Eastern offset), impact, forecast and previous.

We filter to USD (US market) events scheduled for *today* in US/Eastern time,
and cache the weekly feed in-process so the frontend can poll cheaply.
"""
import time
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

logger = logging.getLogger(__name__)

FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
EASTERN = ZoneInfo("America/New_York")
CACHE_TTL_SECONDS = 15 * 60  # Feed only changes a few times a day

# Simple in-process cache: {"fetched_at": float, "data": list}
_cache: dict = {"fetched_at": 0.0, "data": None}


def _fetch_feed() -> list[dict]:
    """Fetch the weekly calendar feed, with a 15-minute in-process cache."""
    now = time.time()
    if _cache["data"] is not None and (now - _cache["fetched_at"]) < CACHE_TTL_SECONDS:
        return _cache["data"]

    logger.info("Fetching economic calendar feed")
    resp = requests.get(
        FEED_URL,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (PreMarketDashboard)"},
    )
    resp.raise_for_status()
    data = resp.json()

    _cache["data"] = data
    _cache["fetched_at"] = now
    return data


def get_us_calendar_today() -> list[dict]:
    """Return today's USD economic events (US/Eastern), sorted by time.

    Each item:
        {
            "time": "08:30",              # US/Eastern wall-clock
            "datetime": "2026-07-01T08:30:00-04:00",
            "title": "Core PCE Price Index m/m",
            "impact": "High",             # High | Medium | Low | Holiday
            "forecast": "0.3%",
            "previous": "0.2%",
            "is_upcoming": true
        }
    """
    try:
        feed = _fetch_feed()
    except Exception as e:
        logger.warning(f"Could not fetch economic calendar: {e}")
        return []

    now_et = datetime.now(EASTERN)
    today = now_et.date()
    events = []

    for entry in feed:
        if entry.get("country") != "USD":
            continue

        raw_date = entry.get("date")
        if not raw_date:
            continue

        try:
            dt = datetime.fromisoformat(raw_date).astimezone(EASTERN)
        except (TypeError, ValueError):
            continue

        if dt.date() != today:
            continue

        events.append({
            "time": dt.strftime("%H:%M"),
            "datetime": dt.isoformat(),
            "title": entry.get("title", ""),
            "impact": entry.get("impact") or "Low",
            "forecast": entry.get("forecast") or "",
            "previous": entry.get("previous") or "",
            "is_upcoming": dt >= now_et,
        })

    events.sort(key=lambda e: e["datetime"])
    logger.info(f"Economic calendar: {len(events)} US events today")
    return events
