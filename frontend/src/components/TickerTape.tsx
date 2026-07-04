import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface TapeQuote {
  symbol: string
  label: string
  kind: 'index' | 'fx' | 'watchlist' | string
  price?: number | null
  change?: number | null
  change_pct?: number | null
}
interface TapeResponse {
  as_of?: string | null
  quotes: TapeQuote[]
}

function fmtPrice(kind: string, p?: number | null): string {
  if (p == null) return '—'
  const digits = kind === 'fx' ? 4 : 2
  return p.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

function fmtPct(pct?: number | null): string {
  if (pct == null) return '—'
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}

export default function TickerTape() {
  const { data } = useQuery<TapeResponse>({
    queryKey: ['ticker-tape'],
    queryFn: () => apiClient.get('/ticker-tape').then(r => r.data),
    refetchInterval: 60_000,      // refresh prices every minute
    staleTime: 55_000,
  })

  const quotes = data?.quotes ?? []
  if (quotes.length === 0) return null

  // Duplicate the sequence so the -50% scroll loops seamlessly. Speed scales
  // with how many symbols there are, so a short watchlist doesn't crawl.
  const items = [...quotes, ...quotes]
  const durationSec = Math.max(quotes.length * 4.5, 30)

  return (
    <div className="ticker-tape" aria-label="Live market ticker">
      <div className="ticker-track" style={{ animationDuration: `${durationSec}s` }}>
        {items.map((q, i) => {
          const up = (q.change_pct ?? 0) >= 0
          return (
            <span className="tape-item" key={`${q.symbol}-${i}`} aria-hidden={i >= quotes.length}>
              <span className="tape-sym">{q.label}</span>
              <span className="tape-price">{fmtPrice(q.kind, q.price)}</span>
              <span className={`tape-chg ${up ? 'up' : 'down'}`}>
                <span className="tape-arrow">{up ? '▲' : '▼'}</span>
                {fmtPct(q.change_pct)}
              </span>
            </span>
          )
        })}
      </div>
    </div>
  )
}
