"""Candidate outcome tracking — did flagged candidates actually move?

We record one outcome row per (symbol, day) when a stock passes screening,
then later evaluate its return 1 trading day and 1 trading week afterwards.
Evaluation is lazy + throttled so viewing the performance panel refreshes
anything that has come due, without hammering yfinance on every poll.
"""
import time
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import CandidateOutcome, Ticker

logger = logging.getLogger(__name__)

_EVAL_THROTTLE_SECONDS = 300  # Don't re-evaluate more than once every 5 min
_last_eval = 0.0


def record_candidate_outcomes(db: Session, scan_id: int, candidates: list[dict]) -> None:
    """Record an outcome row for each screened candidate (deduped per day).

    `candidates` is a list of market-data dicts (must have 'ticker' and 'price').
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    for data in candidates:
        symbol = data["ticker"]
        existing = (
            db.query(CandidateOutcome)
            .filter(
                CandidateOutcome.symbol == symbol,
                CandidateOutcome.flagged_at >= today_start,
            )
            .first()
        )
        if existing:
            continue

        ticker_obj = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        db.add(CandidateOutcome(
            ticker_id=ticker_obj.id if ticker_obj else None,
            scan_id=scan_id,
            symbol=symbol,
            entry_price=data["price"],
            flagged_at=datetime.utcnow(),
        ))

    db.commit()


def _returns_from_history(hist: pd.DataFrame, flagged_at: datetime, entry: float):
    """Return (price_1d, ret_1d, price_1w, ret_1w) using trading-day offsets."""
    if hist is None or hist.empty:
        return None, None, None, None

    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)

    closes = hist["Close"].dropna()
    flagged_date = flagged_at.date()

    # Index position of the entry day (last trading day on/before flag date)
    on_or_before = [i for i, ts in enumerate(closes.index) if ts.date() <= flagged_date]
    if not on_or_before:
        return None, None, None, None
    entry_idx = on_or_before[-1]

    def price_at(offset: int):
        pos = entry_idx + offset
        if 0 <= pos < len(closes):
            return float(closes.iloc[pos])
        return None

    price_1d = price_at(1)
    price_1w = price_at(5)
    ret_1d = round((price_1d - entry) / entry * 100, 2) if price_1d and entry else None
    ret_1w = round((price_1w - entry) / entry * 100, 2) if price_1w and entry else None
    return price_1d, ret_1d, price_1w, ret_1w


def evaluate_pending_outcomes(force: bool = False) -> None:
    """Fill in 1-day / 1-week returns for outcomes whose window has elapsed."""
    global _last_eval
    now = time.time()
    if not force and (now - _last_eval) < _EVAL_THROTTLE_SECONDS:
        return
    _last_eval = now

    db = SessionLocal()
    try:
        pending = (
            db.query(CandidateOutcome)
            .filter(or_(
                CandidateOutcome.evaluated_1d == False,  # noqa: E712
                CandidateOutcome.evaluated_1w == False,  # noqa: E712
            ))
            .all()
        )
        if not pending:
            return

        now_dt = datetime.utcnow()
        symbols = {o.symbol for o in pending}
        history: dict[str, pd.DataFrame] = {}
        for sym in symbols:
            try:
                history[sym] = yf.download(sym, period="2mo", progress=False, threads=False)
            except Exception as e:
                logger.warning(f"Outcome history fetch failed for {sym}: {e}")

        changed = 0
        for o in pending:
            hist = history.get(o.symbol)
            price_1d, ret_1d, price_1w, ret_1w = _returns_from_history(hist, o.flagged_at, o.entry_price)
            age = now_dt - o.flagged_at

            if not o.evaluated_1d and age >= timedelta(days=1) and price_1d is not None:
                o.price_1d, o.return_1d_pct, o.evaluated_1d = price_1d, ret_1d, True
                changed += 1
            if not o.evaluated_1w and age >= timedelta(days=7) and price_1w is not None:
                o.price_1w, o.return_1w_pct, o.evaluated_1w = price_1w, ret_1w, True
                changed += 1

        if changed:
            db.commit()
            logger.info(f"Evaluated {changed} candidate outcome field(s)")
    finally:
        db.close()


def get_outcomes_summary(limit: int = 40) -> dict:
    """Return aggregate performance stats + recent outcomes."""
    evaluate_pending_outcomes()

    db = SessionLocal()
    try:
        rows = (
            db.query(CandidateOutcome)
            .order_by(CandidateOutcome.flagged_at.desc())
            .limit(limit)
            .all()
        )

        r1d = [o.return_1d_pct for o in rows if o.evaluated_1d and o.return_1d_pct is not None]
        r1w = [o.return_1w_pct for o in rows if o.evaluated_1w and o.return_1w_pct is not None]

        def stats(values):
            if not values:
                return {"count": 0, "win_rate": None, "avg_return": None}
            wins = sum(1 for v in values if v > 0)
            return {
                "count": len(values),
                "win_rate": round(wins / len(values) * 100, 1),
                "avg_return": round(sum(values) / len(values), 2),
            }

        return {
            "total": len(rows),
            "pending": sum(1 for o in rows if not o.evaluated_1d),
            "stats_1d": stats(r1d),
            "stats_1w": stats(r1w),
            "outcomes": [
                {
                    "symbol": o.symbol,
                    "flagged_at": o.flagged_at,
                    "entry_price": o.entry_price,
                    "return_1d_pct": o.return_1d_pct,
                    "return_1w_pct": o.return_1w_pct,
                    "evaluated_1d": o.evaluated_1d,
                    "evaluated_1w": o.evaluated_1w,
                }
                for o in rows
            ],
        }
    finally:
        db.close()
