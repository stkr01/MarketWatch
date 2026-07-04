"""Claude analysis of a news article: Swedish summary + affected assets + score."""
from __future__ import annotations

import json
import logging

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)


def _parse_json(raw: str) -> dict:
    """Parse Claude's reply into a dict, tolerating code fences / stray text."""
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s[3:] else s[3:]
        if s.lstrip().lower().startswith("json"):
            s = s.lstrip()[4:]
    s = s.strip().strip("`").strip()
    try:
        return json.loads(s)
    except Exception:
        i, j = s.find("{"), s.rfind("}")
        if i >= 0 and j > i:
            return json.loads(s[i:j + 1])
        raise


def analyze_news(text: str, title: str | None = None, watchlist: set[str] | None = None) -> dict:
    """Return {summary, overall, assets:[{symbol,name,direction,impact_score,rationale}]}."""
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    wl = ", ".join(sorted(watchlist)) if watchlist else "—"

    prompt = f"""Du är en erfaren finansanalytiker. Analysera nyhetsartikeln nedan och svara ENDAST med giltig JSON (ingen markdown, inga kodstaket, ingen text utanför JSON).

Rubrik: {title or "(okänd)"}
Användarens bevakningslista (tickers): {wl}

Artikeltext:
\"\"\"
{text}
\"\"\"

Returnera exakt denna struktur:
{{
  "summary": "2-4 meningars sammanfattning av nyheten på svenska",
  "overall": "1-2 meningar om övergripande marknadspåverkan, på svenska",
  "assets": [
    {{
      "symbol": "Yahoo Finance-ticker (t.ex. NVDA, TSLA, ^GSPC, BTC-USD, GC=F)",
      "name": "bolagets/tillgångens namn",
      "direction": "bullish | bearish | neutral",
      "impact_score": <heltal 1-5>,
      "rationale": "kort motivering på svenska"
    }}
  ]
}}

Regler:
- Max 6 assets, mest påverkade först.
- Använd riktiga Yahoo Finance-tickers.
- impact_score: 1 = marginell, 3 = märkbar, 5 = stor kursdrivande påverkan.
- Om inga enskilda bolag påverkas, ta med relevanta index/ETF:er/råvaror, annars tom lista.
- Prioritera assets som finns i användarens bevakningslista om de är relevanta."""

    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1400,
        messages=[{"role": "user", "content": prompt}],
    )

    data = _parse_json(resp.content[0].text)

    # Normalise / harden the shape.
    data.setdefault("summary", "")
    data.setdefault("overall", "")
    assets = data.get("assets") or []
    clean = []
    for a in assets[:6]:
        try:
            score = int(a.get("impact_score", 0))
        except (TypeError, ValueError):
            score = 0
        clean.append({
            "symbol": (a.get("symbol") or "").upper(),
            "name": a.get("name") or a.get("symbol") or "",
            "direction": (a.get("direction") or "neutral").lower(),
            "impact_score": max(1, min(5, score)) if score else 0,
            "rationale": a.get("rationale") or "",
        })
    data["assets"] = clean
    data["usage_tokens"] = resp.usage.input_tokens + resp.usage.output_tokens
    return data
