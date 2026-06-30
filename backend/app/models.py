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
    price = Column(Float)
    ema_100 = Column(Float, nullable=True)
    above_ema_100 = Column(Boolean, nullable=True)

    has_news = Column(Boolean, default=False)
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
