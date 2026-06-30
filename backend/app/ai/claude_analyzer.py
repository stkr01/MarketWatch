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

Be concise and actionable."""

    response = client.messages.create(
        model="claude-opus-4-1",
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
