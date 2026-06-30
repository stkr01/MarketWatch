from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TickerBase(BaseModel):
    symbol: str
    name: str
    exchange: str
    market_cap: Optional[float] = None


class TickerResponse(TickerBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class ScanResultBase(BaseModel):
    gap_pct: float
    volume: float
    price: float
    ema_100: Optional[float] = None
    above_ema_100: Optional[bool] = None
    has_news: bool


class ScanResultResponse(ScanResultBase):
    id: int
    ticker_id: int
    timestamp: datetime
    ticker: TickerResponse

    class Config:
        from_attributes = True


class ScanBase(BaseModel):
    status: str = "completed"
    candidate_count: int = 0


class ScanResponse(ScanBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class NewsItemBase(BaseModel):
    title: str
    source: str
    url: str
    published_at: datetime


class NewsItemResponse(NewsItemBase):
    id: int
    ticker_id: int
    fetched_at: datetime

    class Config:
        from_attributes = True


class AIAnalysisBase(BaseModel):
    response: str
    usage_tokens: Optional[int] = None


class AIAnalysisResponse(AIAnalysisBase):
    id: int
    ticker_id: int
    requested_at: datetime
    prompt_version: str

    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    ticker: TickerResponse
    scan_result: ScanResultResponse
    has_news: bool
    latest_analysis: Optional[AIAnalysisResponse] = None


class ScanStatusResponse(BaseModel):
    last_scan: Optional[datetime] = None
    next_scan: Optional[datetime] = None
    is_running: bool = False
