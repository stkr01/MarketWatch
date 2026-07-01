"""Claude-generated morning briefing for the trading day."""
from anthropic import Anthropic
from app.config import settings

MODEL = "claude-opus-4-8"


def generate_briefing(candidates: list[dict], econ_events: list[dict]) -> dict:
    """Produce a concise pre-market briefing from candidates + economic calendar.

    Returns {"content": str, "usage_tokens": int}.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    if candidates:
        cand_lines = "\n".join(
            f"- {c['symbol']}: gap {c['gap_pct']:+.2f}%, RVOL {c.get('rvol') or 'n/a'}, "
            f"RSI {c.get('rsi_14') or 'n/a'}, {'news' if c.get('has_news') else 'no news'}, "
            f"{'above' if c.get('above_ema_100') else 'below'} EMA100"
            for c in candidates
        )
    else:
        cand_lines = "(no candidates passed screening this morning)"

    if econ_events:
        econ_lines = "\n".join(
            f"- {e['time']} ET [{e['impact']}] {e['title']}"
            + (f" (forecast {e['forecast']})" if e.get("forecast") else "")
            for e in econ_events
        )
    else:
        econ_lines = "(no scheduled US economic releases today)"

    prompt = f"""You are a pre-market swing trading assistant. Write a concise morning briefing (swing trades, 1–30 day holds, US equities).

SCREENED CANDIDATES:
{cand_lines}

TODAY'S US ECONOMIC CALENDAR:
{econ_lines}

Write the briefing with these short sections:
1. **Market Setup** — 1–2 sentences on the day's tone given the economic calendar (call out high-impact events and their timing).
2. **Top Candidates** — for the 2–3 most interesting screened names, one line each on why (catalyst + technical), or say none stand out.
3. **Watch-outs** — key risks or timing (e.g. events that could whipsaw price).

Be direct and actionable. Do not give financial advice disclaimers. Keep it under 220 words."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "content": response.content[0].text,
        "usage_tokens": response.usage.input_tokens + response.usage.output_tokens,
    }
