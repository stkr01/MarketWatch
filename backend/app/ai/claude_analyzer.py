"""Claude AI analysis for stock candidates"""
from anthropic import Anthropic
from app.config import settings


def analyze_stock_candidate(
    ticker: str,
    market_data: dict,
    news_items: list[dict],
    previous_analysis: str = None
) -> dict:
    """
    Request Claude analysis for a stock candidate

    Returns:
        {
            "ticker": str,
            "response": str,
            "usage_tokens": int
        }
    """
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Build context for Claude
    gap_direction = "up" if market_data["gap_pct"] > 0 else "down"
    ema_position = "above" if market_data["above_ema_100"] else "below"

    news_summary = ""
    if news_items:
        news_summary = "\n\nRecent News:\n"
        for item in news_items[:5]:  # Top 5 news items
            news_summary += f"- {item['title']} ({item['source']})\n"

    context = f"""
Stock: {ticker}
Gap: {market_data['gap_pct']:.2f}% {gap_direction}
Price: ${market_data['price']:.2f}
Volume: {market_data['volume']:,.0f} (avg 20d: {market_data['volume_avg_20']:,.0f})
EMA100: ${market_data['ema_100']:.2f} (Price is {ema_position})
{news_summary}
"""

    prompt = f"""You are a swing trading analyst. Based on the pre-market data below, provide a brief analysis (2-3 sentences) on whether this stock is a good swing trade candidate.

{context}

Focus on:
1. The catalyst (news/catalyst event)
2. Technical setup (gap, volume, EMA100 position)
3. Risk/reward assessment

Be concise and actionable. Svara på svenska."""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return {
        "ticker": ticker,
        "response": response.content[0].text,
        "usage_tokens": response.usage.input_tokens + response.usage.output_tokens
    }


def _client() -> Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")
    return Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def explain_gap(ticker: str, market_data: dict, news_items: list[dict]) -> dict:
    """One-paragraph 'why is this gapping?' — likely catalyst from news + data."""
    client = _client()

    news_summary = "No recent headlines found."
    if news_items:
        news_summary = "\n".join(
            f"- {n['title']} ({n['source']})" for n in news_items[:6]
        )

    gap = market_data.get("gap_pct", 0.0)
    rvol = market_data.get("rvol")
    prompt = f"""You are a pre-market trading analyst. In 2-3 sentences, explain the MOST LIKELY reason {ticker} is gapping {gap:+.2f}% pre-market and whether volume confirms it.

Data:
- Gap: {gap:+.2f}%
- Relative volume (RVOL): {rvol if rvol is not None else 'n/a'}
- Price: ${market_data.get('price', 0):.2f}

Recent headlines:
{news_summary}

If there is no clear catalyst in the headlines, say so plainly (e.g. sympathy move, sector rotation, or no obvious news). Be specific and concise; do not give financial advice disclaimers. Svara på svenska."""

    resp = client.messages.create(
        model="claude-opus-4-8", max_tokens=250,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "ticker": ticker,
        "response": resp.content[0].text,
        "usage_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
    }


def generate_trade_plan(ticker: str, market_data: dict, levels: dict) -> dict:
    """Short swing trade-plan commentary around pre-computed ATR-based levels."""
    client = _client()

    prompt = f"""You are a disciplined swing trader. Write a concise trade plan (3-4 sentences) for {ticker} based on the setup and the pre-computed levels below. Comment on the setup quality, what would confirm or invalidate the trade, and position/risk sizing in general terms (R multiples).

Setup:
- Direction: {levels['direction']}
- Gap: {market_data.get('gap_pct', 0):+.2f}%
- RVOL: {market_data.get('rvol', 'n/a')}
- RSI(14): {market_data.get('rsi_14', 'n/a')}
- Price vs EMA100: {'above' if market_data.get('above_ema_100') else 'below'}
- ATR(14): {levels['atr_used']:.2f}

Levels (already calculated, do NOT recompute):
- Entry ~ ${levels['entry']:.2f}
- Stop ${levels['stop']:.2f}
- Target ${levels['target']:.2f}  (reward:risk ≈ {levels['rr']:.1f}R)

Be direct and actionable. It's fine to say the setup is weak/avoid if the data warrants. Svara på svenska."""

    resp = client.messages.create(
        model="claude-opus-4-8", max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "ticker": ticker,
        "response": resp.content[0].text,
        "usage_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
    }
