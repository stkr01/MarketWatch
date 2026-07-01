import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { yahooUrl } from '../utils'

interface Stats { count: number; win_rate: number | null; avg_return: number | null }
interface Outcome {
  symbol: string
  flagged_at: string
  entry_price: number
  return_1d_pct: number | null
  return_1w_pct: number | null
  evaluated_1d: boolean
}
interface Data {
  total: number
  pending: number
  stats_1d: Stats
  stats_1w: Stats
  outcomes: Outcome[]
}

const retColor = (v: number | null) =>
  v == null ? 'var(--text-dim)' : v > 0 ? 'var(--up)' : v < 0 ? 'var(--down)' : 'var(--text)'

const fmt = (v: number | null) =>
  v == null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(1)}%`

function StatBlock({ label, s }: { label: string; s: Stats }) {
  return (
    <div className="perf-stat">
      <div className="perf-stat-label">{label}</div>
      <div className="perf-stat-win" style={{ color: retColor(s.avg_return) }}>
        {s.win_rate != null ? `${s.win_rate.toFixed(0)}%` : '—'}
      </div>
      <div className="perf-stat-sub">
        win rate · avg <span style={{ color: retColor(s.avg_return) }}>{fmt(s.avg_return)}</span>
        {s.count > 0 && <span className="perf-n"> ({s.count})</span>}
      </div>
    </div>
  )
}

export default function ScreenerPerformance() {
  const { data, isLoading } = useQuery<Data>({
    queryKey: ['outcomes'],
    queryFn: () => apiClient.get('/outcomes').then(r => r.data),
    refetchInterval: 5 * 60 * 1000,
  })

  return (
    <div className="panel" style={{ marginBottom: '1.5rem' }}>
      <div className="panel-header">
        <div className="panel-title">
          📈 Screener Performance
          {data && data.total > 0 && <span className="count">{data.total}</span>}
        </div>
      </div>

      {isLoading ? (
        <div className="loading" style={{ padding: '1.25rem' }}><span className="spinner" />Loading…</div>
      ) : !data || data.total === 0 ? (
        <div className="empty" style={{ padding: '1.25rem' }}>
          No tracked candidates yet
          <small>Flagged candidates are measured 1 day &amp; 1 week later</small>
        </div>
      ) : (
        <>
          <div className="perf-stats">
            <StatBlock label="1 Day" s={data.stats_1d} />
            <StatBlock label="1 Week" s={data.stats_1w} />
          </div>

          <div className="perf-list">
            {data.outcomes.slice(0, 8).map((o, i) => (
              <div className="perf-row" key={`${o.symbol}-${o.flagged_at}-${i}`}>
                <a className="ticker-link" href={yahooUrl(o.symbol)} target="_blank" rel="noopener noreferrer">
                  {o.symbol}
                </a>
                <span className="perf-date">
                  {new Date(o.flagged_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                </span>
                <span className="perf-ret" style={{ color: retColor(o.return_1d_pct) }}>
                  {o.evaluated_1d ? fmt(o.return_1d_pct) : <span className="perf-pending">pending</span>}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
