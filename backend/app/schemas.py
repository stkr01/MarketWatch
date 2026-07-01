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

    model_config = {"from_attributes": True}


class ScanResultBase(BaseModel):
    gap_pct: float
    volume: float
    volume_avg_20: Optional[float] = None
    rvol: Optional[float] = None
    price: float
    ema_100: Optional[float] = None
    above_ema_100: Optional[bool] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    atr_pct: Optional[float] = None
    has_news: bool


class ScanResultResponse(ScanResultBase):
    id: int
    ticker_id: int
    timestamp: datetime
    ticker: TickerResponse

    model_config = {"from_attributes": True}


class ScanMetricsResponse(ScanResultBase):
    """Latest scan metrics for a single ticker (no nested relations)."""
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class ScanBase(BaseModel):
    status: str = "completed"
    candidate_count: int = 0


class ScanResponse(ScanBase):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class NewsItemBase(BaseModel):
    title: str
    source: str
    url: str
    published_at: datetime


class NewsItemResponse(NewsItemBase):
    id: int
    ticker_id: int
    fetched_at: datetime

    model_config = {"from_attributes": True}


class AIAnalysisBase(BaseModel):
    response: str
    usage_tokens: Optional[int] = None


class AIAnalysisResponse(AIAnalysisBase):
    id: int
    ticker_id: int
    requested_at: datetime
    prompt_version: str

    model_config = {"from_attributes": True}


class CandidateResponse(BaseModel):
    ticker: TickerResponse
    scan_result: ScanResultResponse
    has_news: bool
    latest_analysis: Optional[AIAnalysisResponse] = None


class ScanStatusResponse(BaseModel):
    last_scan: Optional[datetime] = None
    next_scan: Optional[datetime] = None
    is_running: bool = False


class BriefingResponse(BaseModel):
    date: str
    content: Optional[str] = None
    generated_at: Optional[datetime] = None
    usage_tokens: Optional[int] = None


class OutcomeItem(BaseModel):
    symbol: str
    flagged_at: datetime
    entry_price: float
    return_1d_pct: Optional[float] = None
    return_1w_pct: Optional[float] = None
    evaluated_1d: bool = False
    evaluated_1w: bool = False


class OutcomeStats(BaseModel):
    count: int = 0
    win_rate: Optional[float] = None
    avg_return: Optional[float] = None


class OutcomesResponse(BaseModel):
    total: int = 0
    pending: int = 0
    stats_1d: OutcomeStats = OutcomeStats()
    stats_1w: OutcomeStats = OutcomeStats()
    outcomes: list[OutcomeItem] = []


class WatchlistItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None

    model_config = {"from_attributes": True}


class WatchlistAdd(BaseModel):
    symbol: str


class EconomicEventResponse(BaseModel):
    time: str
    datetime: datetime
    title: str
    impact: str
    forecast: str = ""
    previous: str = ""
    is_upcoming: bool = False
