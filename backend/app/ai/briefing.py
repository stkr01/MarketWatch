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

    prompt = f"""Du är en assistent för swingtrading före marknadsöppning (swingaffärer, 1–30 dagars innehav, amerikanska aktier). Skriv en kort morgonbriefing PÅ SVENSKA.

SCREENADE KANDIDATER:
{cand_lines}

DAGENS AMERIKANSKA EKONOMISKA KALENDER:
{econ_lines}

Skriv briefingen med dessa korta avsnitt (använd exakt dessa svenska rubriker):
1. **Marknadsläge** — 1–2 meningar om dagens ton givet den ekonomiska kalendern (lyft fram händelser med hög påverkan och deras tidpunkt, ange tider i ET).
2. **Toppkandidater** — för de 2–3 mest intressanta screenade namnen, en rad var om varför (katalysator + teknik), eller skriv att inga sticker ut.
3. **Att bevaka** — viktiga risker eller tidpunkter (t.ex. händelser som kan svänga priset kraftigt).

Var rak och handlingsbar. Använd inga friskrivningar om finansiell rådgivning. Håll dig under 220 ord. Svara enbart på svenska."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "content": response.content[0].text,
        "usage_tokens": response.usage.input_tokens + response.usage.output_tokens,
    }
