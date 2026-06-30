import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface Props {
  onSelectTicker: (ticker: string) => void
  selectedTicker?: string | null
}

export default function CandidateTable({ onSelectTicker, selectedTicker }: Props) {
  const { data: candidates = [], isLoading, error } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => apiClient.get('/candidates').then(r => r.data),
    refetchInterval: 30000, // Poll every 30 seconds
  })

  if (isLoading) return <div className="loading">⟳ Loading candidates...</div>

  if (error) return <div className="loading" style={{ color: '#dc2626' }}>Error loading candidates</div>

  return (
    <div className="candidate-table">
      {candidates.length === 0 ? (
        <div className="loading">
          <p>No candidates found matching criteria yet.</p>
          <small style={{ marginTop: '1rem', display: 'block' }}>Click "Scan Now" to trigger a market scan</small>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Ticker</th>
              <th style={{ textAlign: 'right' }}>Gap %</th>
              <th style={{ textAlign: 'right' }}>Volume</th>
              <th style={{ textAlign: 'center' }}>EMA100</th>
              <th style={{ textAlign: 'center' }}>News</th>
              <th style={{ textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate: any) => {
              const isSelected = selectedTicker === candidate.ticker.symbol
              const gapPct = candidate.scan_result.gap_pct
              const gapColor = gapPct > 0 ? '#16a34a' : '#dc2626'

              return (
                <tr key={candidate.ticker.id} style={{
                  background: isSelected ? 'rgba(37, 99, 235, 0.1)' : undefined,
                  borderLeft: isSelected ? '3px solid #2563eb' : 'none'
                }}>
                  <td style={{ fontWeight: 600, color: '#60a5fa' }}>
                    {candidate.ticker.symbol}
                  </td>
                  <td style={{ textAlign: 'right', color: gapColor, fontWeight: 500 }}>
                    {gapPct > 0 ? '+' : ''}{gapPct.toFixed(2)}%
                  </td>
                  <td style={{ textAlign: 'right', color: '#a1e34a' }}>
                    {(candidate.scan_result.volume / 1e6).toFixed(1)}M
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      background: candidate.scan_result.above_ema_100 ? 'rgba(22, 163, 74, 0.2)' : 'rgba(220, 38, 38, 0.2)',
                      color: candidate.scan_result.above_ema_100 ? '#86efac' : '#fca5a5'
                    }}>
                      {candidate.scan_result.above_ema_100 ? '↑ Above' : '↓ Below'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {candidate.has_news ? (
                      <span style={{ color: '#60a5fa', fontWeight: 600 }}>📰</span>
                    ) : (
                      <span style={{ color: '#64748b' }}>-</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => onSelectTicker(candidate.ticker.symbol)}
                      style={{
                        padding: '0.5rem 1rem',
                        fontSize: '0.85rem',
                        background: isSelected ? '#1d4ed8' : '#2563eb'
                      }}
                    >
                      {isSelected ? 'Selected' : 'View'}
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
