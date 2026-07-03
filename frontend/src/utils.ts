export function yahooUrl(symbol: string): string {
  return `https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}`
}

/** Colour + label for an RSI value. Overbought >70, oversold <30. */
export function rsiZone(rsi?: number | null): { color: string; label: string } {
  if (rsi == null) return { color: 'var(--text-dim)', label: '—' }
  if (rsi >= 70) return { color: '#fda4af', label: rsi.toFixed(0) }   // overbought
  if (rsi <= 30) return { color: '#86efac', label: rsi.toFixed(0) }   // oversold
  return { color: 'var(--text)', label: rsi.toFixed(0) }
}

/** Short badge for where a scan's price came from (backend `price_source`). */
export function priceSourceBadge(
  source?: string | null,
): { label: string; title: string } | null {
  switch (source) {
    case 'premarket':
      return { label: 'PRE', title: 'Live pre-market price (04:00–09:30 ET)' }
    case 'postmarket':
      return { label: 'POST', title: 'Live post-market price (16:00–20:00 ET)' }
    case 'regular':
      return { label: 'LIVE', title: 'Live regular-session price' }
    case 'daily':
      return { label: 'EOD', title: 'Daily close (no intraday quote available)' }
    default:
      return null
  }
}

export type Session = {
  label: string
  cls: 'session-pre' | 'session-open' | 'session-closed'
}

/** Current US market session based on America/New_York wall-clock time. */
export function marketSession(now: Date = new Date()): Session {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: '2-digit',
    minute: '2-digit',
    weekday: 'short',
    hour12: false,
  }).formatToParts(now)

  const get = (t: string) => parts.find(p => p.type === t)?.value ?? ''
  const hour = parseInt(get('hour'), 10)
  const minute = parseInt(get('minute'), 10)
  const weekday = get('weekday')
  const mins = hour * 60 + minute
  const isWeekday = !['Sat', 'Sun'].includes(weekday)

  if (!isWeekday) return { label: 'Market Closed', cls: 'session-closed' }
  if (mins >= 240 && mins < 570) return { label: 'Pre-Market', cls: 'session-pre' }   // 04:00–09:30
  if (mins >= 570 && mins < 960) return { label: 'Market Open', cls: 'session-open' }  // 09:30–16:00
  if (mins >= 960 && mins < 1200) return { label: 'After Hours', cls: 'session-pre' }  // 16:00–20:00
  return { label: 'Market Closed', cls: 'session-closed' }
}
