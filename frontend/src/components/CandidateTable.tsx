import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { yahooUrl, rsiZone, priceSourceBadge } from '../utils'

interface Props {
  onSelectTicker: (ticker: string) => void
  selectedTicker?: string | null
}

export default function CandidateTable({ onSelectTicker, selectedTicker }: Props) {
  const { data: candidates = [], isLoading, error } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => apiClient.get('/candidates').then(r => r.data),
    refetchInterval: 30000,
  })

  if (isLoading) return <div className="loading"><span className="spinner" />Loading candidates…</div>
  if (error) return <div className="empty" style={{ color: '#fda4af' }}>Error loading candidates</div>

  if (candidates.length === 0) {
    return (
      <div className="empty">
        No candidates match the criteria yet.
        <small>Click “Scan Now” to trigger a market scan</small>
      </div>
    )
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Ticker</th>
          <th className="num">Gap %</th>
          <th className="num">Price</th>
          <th className="num">Volume</th>
          <th className="num">RSI</th>
          <th className="center">EMA100</th>
          <th className="center">News</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((c: any) => {
          const sr = c.scan_result
          const isSelected = selectedTicker === c.ticker.symbol
          const up = sr.gap_pct > 0
          const ratio = sr.volume_avg_20 ? sr.volume / sr.volume_avg_20 : null
          const fill = ratio ? Math.min(ratio / 3, 1) * 100 : 0

          return (
            <tr
              key={c.ticker.id}
              className={isSelected ? 'selected' : ''}
              onClick={() => onSelectTicker(c.ticker.symbol)}
            >
              <td>
                <a
                  className="ticker-link"
                  href={yahooUrl(c.ticker.symbol)}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  title="Open on Yahoo Finance"
                >
                  {c.ticker.symbol}<span className="ext">↗</span>
                </a>
              </td>
              <td className="num">
                <span className={`pill ${up ? 'pill-up' : 'pill-down'}`}>
                  {up ? '▲' : '▼'} {up ? '+' : ''}{sr.gap_pct.toFixed(2)}%
                </span>
              </td>
              <td className="num">
                ${sr.price?.toFixed(2)}
                {(() => {
                  const b = priceSourceBadge(sr.price_source)
                  return b ? (
                    <span className="src-badge" title={b.title} style={{ marginLeft: 4 }}>{b.label}</span>
                  ) : null
                })()}
              </td>
              <td className="num">
                <div className="vol-wrap">
                  <span>
                    {(sr.volume / 1e6).toFixed(1)}M
                    {ratio && <small style={{ color: 'var(--text-dim)', marginLeft: 4 }}>{ratio.toFixed(1)}×</small>}
                  </span>
                  {ratio && (
                    <span className="vol-bar"><span className="vol-fill" style={{ width: `${fill}%` }} /></span>
                  )}
                </div>
              </td>
              <td className="num" style={{ color: rsiZone(sr.rsi_14).color, fontWeight: 600 }}>
                {rsiZone(sr.rsi_14).label}
              </td>
              <td className="center">
                <span className={`badge ${sr.above_ema_100 ? 'badge-above' : 'badge-below'}`}>
                  {sr.above_ema_100 ? '↑ Above' : '↓ Below'}
                </span>
              </td>
              <td className="center">
                {c.has_news
                  ? <span title="Has recent news catalyst">📰</span>
                  : <span className="badge-muted">—</span>}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
