import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface Props {
  onSelectTicker: (ticker: string) => void
}

export default function CandidateTable({ onSelectTicker }: Props) {
  const { data: candidates = [], isLoading } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => apiClient.get('/candidates').then(r => r.data),
    refetchInterval: 30000, // Poll every 30 seconds
  })

  if (isLoading) return <div>Loading candidates...</div>

  return (
    <div className="candidate-table">
      <table>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Gap %</th>
            <th>Volume</th>
            <th>EMA100</th>
            <th>News</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate: any) => (
            <tr key={candidate.ticker.id}>
              <td>{candidate.ticker.symbol}</td>
              <td>{candidate.scan_result.gap_pct.toFixed(2)}%</td>
              <td>{(candidate.scan_result.volume / 1e6).toFixed(1)}M</td>
              <td>{candidate.scan_result.above_ema_100 ? 'Above' : 'Below'}</td>
              <td>{candidate.has_news ? '✓' : '-'}</td>
              <td>
                <button onClick={() => onSelectTicker(candidate.ticker.symbol)}>
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {candidates.length === 0 && (
        <p>No candidates found matching criteria.</p>
      )}
    </div>
  )
}
