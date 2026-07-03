import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Pre-Market Dashboard"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: list = ["*"]  # Tailscale private network

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).parent.parent.parent}/data/premarket.db"
    )

    # Market data
    TOP_N_TICKERS: int = 10  # Dev: top 10, can be config later
    SCAN_INTERVAL_MINUTES: int = 5  # Scan every 5 minutes during pre-market
    # Use real pre/post-market intraday quotes for the gap (vs. daily open).
    # When True, gap% is measured against the latest actual pre-market trade.
    USE_PREMARKET_DATA: bool = os.getenv("USE_PREMARKET_DATA", "true").lower() == "true"
    PRE_MARKET_START_HOUR: int = 4  # 04:00 EST
    PRE_MARKET_END_HOUR: int = 9  # 09:30 EST (approximate)
    PRE_MARKET_END_MINUTE: int = 30

    # Swing trading rules (initial defaults, configurable)
    GAP_THRESHOLD_PERCENT: float = 2.0  # ±2% gap
    VOLUME_MULTIPLIER: float = 1.5  # 1.5x of 20-day average
    NEWS_LOOKBACK_HOURS: int = 48  # Last 48 hours for news

    # Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Alerts — notify on strong candidates (a candidate that also clears the
    # tighter thresholds below). Only fires when at least one channel is set.
    ALERTS_ENABLED: bool = os.getenv("ALERTS_ENABLED", "true").lower() == "true"
    ALERT_GAP_THRESHOLD_PERCENT: float = float(os.getenv("ALERT_GAP_THRESHOLD_PERCENT", "4.0"))
    ALERT_RVOL_THRESHOLD: float = float(os.getenv("ALERT_RVOL_THRESHOLD", "2.0"))
    # Telegram: create a bot via @BotFather, then get your chat id.
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    # Discord: a channel webhook URL.
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    # News sources
    NEWS_SOURCES: list = [
        "MarketWatch",
        "CNBC",
        "Yahoo Finance",
        "Google News"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
