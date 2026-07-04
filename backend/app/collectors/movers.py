"""Auto-discover market movers via Yahoo's predefined screeners.

Unlike the watchlist scan (which pulls history per symbol), this reads Yahoo's
ready-made screeners in a few calls and uses the quote fields they already
return — so it surfaces stocks *in play* that aren't on the watchlist yet,
cheaply. The user can then promote interesting ones into the watchlist.
"""
from __future__ import annotations

import logging

from yfinance import screen

logger = logging.getLogger(__name__)

# (screener key, short source label)
SCREENS: list[tuple[str, str]] = [
    ("day_gainers", "gainer"),
    ("day_losers", "loser"),
    ("most_actives", "active"),
    ("small_cap_gainers", "small-cap"),
]


def _normalize(q: dict, source: str) -> dict | None:
    symbol = q.get("symbol")
    if not symbol:
        return None

    state = q.get("marketState")
    pre_c, pre_p = q.get("preMarketChangePercent"), q.get("preMarketPrice")
    post_c, post_p = q.get("postMarketChangePercent"), q.get("postMarketPrice")
    reg_c, reg_p = q.get("regularMarketChangePercent"), q.get("regularMarketPrice")

    # Prefer the session that's actually live so pre-market moves show through.
    if state == "PRE" and pre_c is not None:
        chg, px, sess = pre_c, pre_p, "pre"
    elif state in ("POST", "POSTPOST", "CLOSED") and post_c is not None:
        chg, px, sess = post_c, post_p, "post"
    else:
        chg, px, sess = reg_c, reg_p, "regular"

    vol = q.get("regularMarketVolume")
    adv = q.get("averageDailyVolume10Day") or q.get("averageDailyVolume3Month")
    rvol = round(vol / adv, 2) if vol and adv else None

    return {
        "symbol": symbol,
        "name": q.get("shortName") or q.get("longName") or symbol,
        "price": round(px, 4) if px is not None else None,
        "change_pct": round(chg, 2) if chg is not None else None,
        "volume": vol,
        "rvol": rvol,
        "market_cap": q.get("marketCap"),
        "session": sess,
        "source": source,
    }


def get_movers(per_screen: int = 25, limit: int = 30) -> list[dict]:
    """Merged, de-duped movers across the screeners, ranked by |change%|."""
    seen: dict[str, dict] = {}
    for key, label in SCREENS:
        try:
            result = screen(key, count=per_screen)
        except Exception as e:
            logger.warning(f"Screener '{key}' failed: {e}")
            continue
        for q in (result.get("quotes", []) if isinstance(result, dict) else []):
            m = _normalize(q, label)
            if m and m["symbol"] not in seen and m["change_pct"] is not None:
                seen[m["symbol"]] = m

    movers = sorted(seen.values(), key=lambda m: abs(m["change_pct"]), reverse=True)
    return movers[:limit]
