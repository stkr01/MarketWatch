import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface Props {
  ticker: string
}

export default function AIAnalysisPanel({ ticker }: Props) {
  const [hasRequested, setHasRequested] = useState(false)

  const { data: analysis, isLoading } = useQuery({
    queryKey: ['analysis', ticker],
    queryFn: () => apiClient.post(`/stock/${ticker}/analyze`).then(r => r.data),
    enabled: hasRequested,
  })

  const handleAnalyze = () => {
    setHasRequested(true)
  }

  if (!hasRequested) {
    return (
      <div className="analysis-panel">
        <p>Click button to request Claude AI analysis</p>
        <button onClick={handleAnalyze}>Request Analysis</button>
      </div>
    )
  }

  if (isLoading) {
    return <div className="analysis-panel">Analyzing with Claude...</div>
  }

  if (analysis) {
    return (
      <div className="analysis-panel">
        <h3>Claude Analysis</h3>
        <div className="analysis-content">
          {analysis.response}
        </div>
        <small>Analyzed: {new Date(analysis.requested_at).toLocaleString()}</small>
      </div>
    )
  }

  return <div className="analysis-panel">No analysis available</div>
}
