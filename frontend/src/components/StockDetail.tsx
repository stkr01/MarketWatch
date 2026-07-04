import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import AIAnalysisPanel from './AIAnalysisPanel'
import PriceChart from './PriceChart'
import { yahooUrl, rsiZone, priceSourceBadge } from '../utils'

interface Props {
  ticker: string
}

export default function StockDetail({ ticker }: Props) {
  const { data: stock, isLoading: stockLoading } = useQuery({
    queryKey: ['stock', ticker],
    queryFn: () => apiClient.get(`/stock/${ticker}`).then(r => r.data),
    enabled: !!ticker,
  })

  const { data: metrics } = useQuery({
    queryKey: ['scan-metrics', ticker],
    queryFn: () => apiClient.get(`/stock/${ticker}/scan`).then(r => r.data),
    enabled: !!ticker,
    retry: false,
  })

  const { data: news = [] } = useQuery({
    queryKey: ['news', ticker],
    queryFn: () => apiClient.get(`/news/${ticker}`).then(r => r.data),
    enabled: !!ticker,
  })

  if (stockLoading) return <div className="loading"><span className="spinner" />Loading stock details…</div>

  return (
    <div className="stock-detail">
      <div className="detail-head" style={{ marginBottom: '1.5rem' }}>
        <div>
          <div className="detail-name">{stock?.name || ticker}</div>
          <div className="detail-meta">
            {stock?.exchange || '—'}
            {' · Market Cap: '}
            {stock?.market_cap ? `$${(stock.market_cap / 1e9).toFixed(1)}B` : 'N/A'}
          </div>
        </div>
        <a className="btn-ghost btn-sm" href={yahooUrl(ticker)} target="_blank" rel="noopener noreferrer"
           style={{ textDecoration: 'none' }}>
          Yahoo Finance ↗
        </a>
      </div>

      <div className="section-label" style={{ marginBottom: '0.6rem' }}>📈 Intraday (inkl. pre-market)</div>
      <PriceChart ticker={ticker} />

      {metrics && (
        <div className="metric-grid" style={{ marginTop: '1.5rem' }}>
          <div className="metric">
            <div className="metric-label">Gap</div>
            <div className="metric-val" style={{ color: metrics.gap_pct >= 0 ? 'var(--up)' : 'var(--down)' }}>
              {metrics.gap_pct >= 0 ? '+' : ''}{metrics.gap_pct.toFixed(2)}%
            </div>
            {metrics.previous_close != null && (
              <small style={{ color: 'var(--text-dim)' }}>vs ${metrics.previous_close.toFixed(2)} close</small>
            )}
          </div>
          <div className="metric">
            <div className="metric-label">Price</div>
            <div className="metric-val">
              ${metrics.price?.toFixed(2)}
              {(() => {
                const b = priceSourceBadge(metrics.price_source)
                return b ? (
                  <span className="src-badge" title={b.title} style={{ marginLeft: 6 }}>{b.label}</span>
                ) : null
              })()}
            </div>
          </div>
          <div className="metric">
            <div className="metric-label">RVOL</div>
            <div className="metric-val">{metrics.rvol != null ? `${metrics.rvol.toFixed(2)}×` : '—'}</div>
          </div>
          <div className="metric">
            <div className="metric-label">RSI (14)</div>
            <div className="metric-val" style={{ color: rsiZone(metrics.rsi_14).color }}>
              {rsiZone(metrics.rsi_14).label}
            </div>
          </div>
          <div className="metric">
            <div className="metric-label">ATR (14)</div>
            <div className="metric-val">
              {metrics.atr_14 != null ? `$${metrics.atr_14.toFixed(2)}` : '—'}
              {metrics.atr_pct != null && <small style={{ color: 'var(--text-dim)' }}> ({metrics.atr_pct.toFixed(1)}%)</small>}
            </div>
          </div>
          <div className="metric">
            <div className="metric-label">EMA 100</div>
            <div className="metric-val" style={{ color: metrics.above_ema_100 ? 'var(--up)' : 'var(--down)' }}>
              {metrics.above_ema_100 ? '↑ Above' : '↓ Below'}
            </div>
          </div>
        </div>
      )}

      <AIAnalysisPanel ticker={ticker} />

      <div style={{ marginTop: '1.75rem' }}>
        <div className="section-label">📰 Recent News{news.length ? ` (${news.length})` : ''}</div>
        {news.length === 0 ? (
          <p style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>No recent news found for this ticker</p>
        ) : (
          <div className="news-list">
            {news.slice(0, 6).map((item: any) => (
              <div key={item.id} className="news-item">
                <a href={item.url} target="_blank" rel="noopener noreferrer">{item.title}</a>
                <div className="news-meta">
                  <span className="news-src">📍 {item.source}</span>
                  <span className="news-date">{new Date(item.published_at).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
