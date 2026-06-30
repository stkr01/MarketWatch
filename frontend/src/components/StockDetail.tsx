import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import AIAnalysisPanel from './AIAnalysisPanel'

interface Props {
  ticker: string
}

export default function StockDetail({ ticker }: Props) {
  const [showAnalysis, setShowAnalysis] = useState(false)

  const { data: stock, isLoading: stockLoading } = useQuery({
    queryKey: ['stock', ticker],
    queryFn: () => apiClient.get(`/stock/${ticker}`).then(r => r.data),
    enabled: !!ticker
  })

  const { data: news = [], isLoading: newsLoading } = useQuery({
    queryKey: ['news', ticker],
    queryFn: () => apiClient.get(`/news/${ticker}`).then(r => r.data),
    enabled: !!ticker
  })

  if (stockLoading) return <div className="loading">Loading stock details...</div>

  return (
    <div className="stock-detail">
      <div style={{ marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid #475569' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>
              {stock?.name || ticker}
            </h3>
            <p style={{ color: '#94a3b8' }}>
              {stock?.exchange} • Market Cap: {stock?.market_cap ? `$${(stock.market_cap / 1e9).toFixed(1)}B` : 'N/A'}
            </p>
          </div>
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            style={{
              padding: '0.75rem 1.5rem',
              background: showAnalysis ? '#1d4ed8' : '#2563eb'
            }}
          >
            {showAnalysis ? '✓ Analyzing' : '🤖 Analyze'}
          </button>
        </div>
      </div>

      {news && news.length > 0 && (
        <div className="news-section">
          <h3 style={{ marginBottom: '1rem' }}>📰 Recent News ({news.length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {news.slice(0, 5).map((item: any) => (
              <div key={item.id} style={{
                padding: '1rem',
                background: '#1e293b',
                borderRadius: '8px',
                borderLeft: '3px solid #2563eb'
              }}>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: '#60a5fa',
                    textDecoration: 'none',
                    wordBreak: 'break-word',
                    display: 'block',
                    marginBottom: '0.5rem'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                  onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                >
                  {item.title}
                </a>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: '#a1e34a', fontWeight: 500 }}>📍 {item.source}</span>
                  <span style={{ color: '#64748b' }}>
                    {new Date(item.published_at).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!news || news.length === 0 && (
        <div className="news-section">
          <p style={{ color: '#64748b', fontStyle: 'italic' }}>No recent news found for this ticker</p>
        </div>
      )}

      {showAnalysis && <AIAnalysisPanel ticker={ticker} />}
    </div>
  )
}
