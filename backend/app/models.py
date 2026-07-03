from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


class Ticker(Base):
    __tablename__ = "tickers"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    exchange = Column(String)
    market_cap = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, index=True)  # In the scan watchlist
    last_updated = Column(DateTime, default=datetime.utcnow)

    scan_results = relationship("ScanResult", back_populates="ticker")
    news_items = relationship("NewsItem", back_populates="ticker")
    ai_analyses = relationship("AIAnalysis", back_populates="ticker")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String, default="completed")  # completed, in_progress, failed
    candidate_count = Column(Integer, default=0)

    scan_results = relationship("ScanResult", back_populates="scan")


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    ticker_id = Column(Integer, ForeignKey("tickers.id"))

    gap_pct = Column(Float)
    volume = Column(Float)
    volume_avg_20 = Column(Float, nullable=True)
    rvol = Column(Float, nullable=True)
    price = Column(Float)
    previous_close = Column(Float, nullable=True)  # Gap reference (prior regular close)
    pre_market_price = Column(Float, nullable=True)  # Live intraday quote used for gap
    price_source = Column(String, nullable=True)  # premarket / regular / postmarket / closed / daily
    ema_100 = Column(Float, nullable=True)
    above_ema_100 = Column(Boolean, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    atr_pct = Column(Float, nullable=True)

    has_news = Column(Boolean, default=False)
    is_candidate = Column(Boolean, default=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    scan = relationship("Scan", back_populates="scan_results")
    ticker = relationship("Ticker", back_populates="scan_results")


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"))

    title = Column(String)
    source = Column(String)
    url = Column(String)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    ticker = relationship("Ticker", back_populates="news_items")


class CandidateOutcome(Base):
    """Tracks a stock that passed screening, to measure how it performed."""
    __tablename__ = "candidate_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"))
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    symbol = Column(String, index=True)

    flagged_at = Column(DateTime, default=datetime.utcnow, index=True)
    entry_price = Column(Float)  # Price when flagged as candidate

    price_1d = Column(Float, nullable=True)
    return_1d_pct = Column(Float, nullable=True)
    evaluated_1d = Column(Boolean, default=False)

    price_1w = Column(Float, nullable=True)
    return_1w_pct = Column(Float, nullable=True)
    evaluated_1w = Column(Boolean, default=False)

    ticker = relationship("Ticker")


class Briefing(Base):
    """Cached Claude-generated morning briefing (one per ET calendar day)."""
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)  # YYYY-MM-DD (US/Eastern)
    content = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    usage_tokens = Column(Integer, nullable=True)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"))

    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    prompt_version = Column(String, default="v1")
    response = Column(Text)
    usage_tokens = Column(Integer, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    ticker = relationship("Ticker", back_populates="ai_analyses")
