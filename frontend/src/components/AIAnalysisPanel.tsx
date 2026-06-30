import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface Props {
  ticker: string
}

export default function AIAnalysisPanel({ ticker }: Props) {
  const [hasRequested, setHasRequested] = useState(false)
  const queryClient = useQueryClient()

  const { data: analysis, isLoading, error, isFetched } = useQuery({
    queryKey: ['analysis', ticker],
    queryFn: () => apiClient.post(`/stock/${ticker}/analyze`).then(r => r.data),
    enabled: hasRequested,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })

  const handleAnalyze = () => {
    setHasRequested(true)
  }

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['analysis', ticker] })
    setHasRequested(true)
  }

  return (
    <div className="analysis-panel" style={{
      marginTop: '2rem',
      padding: '1.5rem',
      background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(59, 130, 246, 0.05))',
      border: '1px solid #3b82f6',
      borderRadius: '8px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ color: '#60a5fa' }}>🤖 Claude AI Analysis</h3>
        {isFetched && !isLoading && (
          <button
            onClick={handleRefresh}
            style={{
              padding: '0.5rem 1rem',
              fontSize: '0.85rem',
              background: '#334155'
            }}
          >
            ↻ Refresh
          </button>
        )}
      </div>

      {!hasRequested ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
          <p style={{ marginBottom: '1rem' }}>Ready to analyze {ticker}?</p>
          <p style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Claude will examine gaps, volume, EMA trends, and news catalysts
          </p>
          <button
            onClick={handleAnalyze}
            style={{
              padding: '0.75rem 2rem',
              fontSize: '1rem',
              background: '#2563eb'
            }}
          >
            Generate Analysis
          </button>
        </div>
      ) : isLoading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
          <p>⟳ Claude is analyzing {ticker}...</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', color: '#64748b' }}>
            This typically takes 3-5 seconds
          </p>
        </div>
      ) : error ? (
        <div style={{
          padding: '1.5rem',
          background: 'rgba(220, 38, 38, 0.1)',
          border: '1px solid #dc2626',
          borderRadius: '6px',
          color: '#fca5a5'
        }}>
          <p>Failed to analyze. Please try again.</p>
          <button
            onClick={handleRefresh}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              fontSize: '0.85rem',
              background: '#dc2626'
            }}
          >
            Retry
          </button>
        </div>
      ) : analysis ? (
        <div>
          <div className="analysis-content" style={{
            padding: '1.5rem',
            background: '#0f172a',
            borderRadius: '6px',
            marginBottom: '1rem',
            lineHeight: '1.8'
          }}>
            {analysis.response}
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.85rem',
            color: '#64748b'
          }}>
            <span>
              ✓ Analyzed {new Date(analysis.requested_at).toLocaleTimeString()}
            </span>
            <span>
              Tokens: {analysis.usage_tokens}
            </span>
          </div>
        </div>
      ) : null}
    </div>
  )
}
