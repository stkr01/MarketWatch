"""Push alerts for strong candidates via Telegram and/or Discord webhooks.

A "strong" candidate is one that passed screening AND clears the tighter
alert thresholds (bigger gap + higher RVOL). We send at most one alert per
symbol per Eastern-time day so the scheduler (which scans every few minutes)
doesn't spam the same names.
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app import runtime_config
from app.models import AlertSent

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
_HTTP_TIMEOUT = 10


def _configured_channels() -> list[str]:
    """Which alert channels have credentials configured."""
    channels = []
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        channels.append("telegram")
    if settings.DISCORD_WEBHOOK_URL:
        channels.append("discord")
    return channels


def alerts_status() -> dict:
    """Human-readable config summary (no secrets)."""
    channels = _configured_channels()
    return {
        "enabled": settings.ALERTS_ENABLED,
        "channels": channels,
        "active": settings.ALERTS_ENABLED and bool(channels),
        "gap_threshold_pct": runtime_config.get_float("ALERT_GAP_THRESHOLD_PERCENT"),
        "rvol_threshold": settings.ALERT_RVOL_THRESHOLD,
    }


def _is_strong(data: dict) -> bool:
    """Does a candidate clear the tighter alert thresholds?"""
    gap = abs(data.get("gap_pct") or 0.0)
    rvol = data.get("rvol")
    if gap < runtime_config.get_float("ALERT_GAP_THRESHOLD_PERCENT"):
        return False
    # RVOL may be missing; if present it must clear the bar.
    if rvol is not None and rvol < settings.ALERT_RVOL_THRESHOLD:
        return False
    return True


def _format_message(data: dict) -> str:
    symbol = data["ticker"]
    gap = data.get("gap_pct") or 0.0
    arrow = "🟢▲" if gap >= 0 else "🔴▼"
    rvol = data.get("rvol")
    price = data.get("price")
    src = (data.get("price_source") or "").upper()
    src_tag = f" [{src}]" if src and src != "DAILY" else ""
    lines = [
        f"{arrow} {symbol} gap {gap:+.2f}%",
        f"Price ${price:.2f}{src_tag}" if price is not None else "",
        f"RVOL {rvol:.2f}" if rvol is not None else "",
        f"RSI {data['rsi_14']:.0f}" if data.get("rsi_14") is not None else "",
        f"https://finance.yahoo.com/quote/{symbol}",
    ]
    return "\n".join(l for l in lines if l)


def _send_telegram(text: str) -> bool:
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")
        return False


def _send_discord(text: str) -> bool:
    try:
        resp = requests.post(
            settings.DISCORD_WEBHOOK_URL,
            json={"content": text},
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Discord alert failed: {e}")
        return False


def _dispatch(text: str) -> list[str]:
    """Send to every configured channel; return the channels that succeeded."""
    sent = []
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID and _send_telegram(text):
        sent.append("telegram")
    if settings.DISCORD_WEBHOOK_URL and _send_discord(text):
        sent.append("discord")
    return sent


def _already_alerted_today(db: Session, symbol: str) -> bool:
    today_start = datetime.now(ET).replace(hour=0, minute=0, second=0, microsecond=0)
    # AlertSent.sent_at is stored in UTC (naive); compare against UTC day boundary.
    today_start_utc = today_start.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    return (
        db.query(AlertSent)
        .filter(
            AlertSent.symbol == symbol,
            AlertSent.status != "test",
            AlertSent.sent_at >= today_start_utc,
        )
        .first()
        is not None
    )


def dispatch_candidate_alerts(db: Session, scan_id: int, candidates: list[dict]) -> int:
    """Alert on strong candidates from a scan. Returns the number of alerts sent.

    `candidates` are the market-data dicts for tickers that passed screening.
    Safe to call unconditionally — it no-ops when alerts are disabled or no
    channel is configured, and never raises into the pipeline.
    """
    if not settings.ALERTS_ENABLED:
        return 0
    channels = _configured_channels()
    if not channels:
        return 0

    sent_count = 0
    try:
        for data in candidates:
            symbol = data["ticker"]
            if not _is_strong(data):
                continue
            if _already_alerted_today(db, symbol):
                continue

            text = _format_message(data)
            succeeded = _dispatch(text)
            status = "sent" if len(succeeded) == len(channels) else ("partial" if succeeded else "failed")

            db.add(AlertSent(
                symbol=symbol,
                scan_id=scan_id,
                gap_pct=data.get("gap_pct"),
                rvol=data.get("rvol"),
                price=data.get("price"),
                price_source=data.get("price_source"),
                channels=",".join(succeeded),
                message=text,
                status=status,
            ))
            db.commit()
            if succeeded:
                sent_count += 1
                logger.info(f"Alert sent for {symbol} via {succeeded} ({status})")
    except Exception as e:
        logger.error(f"Alert dispatch error: {e}", exc_info=True)
        db.rollback()

    return sent_count


def send_test_alert(db: Session) -> dict:
    """Send a test notification to all configured channels; record it."""
    channels = _configured_channels()
    if not channels:
        return {"ok": False, "detail": "No alert channel configured", "channels": []}

    text = "✅ Pre-Market Dashboard: test alert — notifications are working."
    succeeded = _dispatch(text)
    db.add(AlertSent(
        symbol="TEST",
        message=text,
        channels=",".join(succeeded),
        status="test",
    ))
    db.commit()
    return {
        "ok": bool(succeeded),
        "channels": succeeded,
        "detail": "Sent" if succeeded else "All configured channels failed",
    }
