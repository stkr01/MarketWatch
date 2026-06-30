import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import AIAnalysisPanel from './AIAnalysisPanel'

interface Props {
  ticker: string
}

export default function StockDetail({ ticker }: Props) {
  const [showAnalysis, setShowAnalysis] = useState(false)

  const { data: stock } = useQuery({
    queryKey: ['stock', ticker],
    queryFn: () => apiClient.get(`/stock/${ticker}`).then(r => r.data),
  })

  const { data: news } = useQuery({
    queryKey: ['news', ticker],
    queryFn: () => apiClient.get(`/news/${ticker}`).then(r => r.data),
  })

  return (
    <div className="stock-detail">
      <div className="detail-header">
        <h2>{ticker}</h2>
        <button onClick={() => setShowAnalysis(!showAnalysis)}>
          {showAnalysis ? 'Hide Analysis' : 'Analyze with Claude'}
        </button>
      </div>

      {stock && (
        <div className="stock-info">
          <p><strong>Price:</strong> ${stock.price?.toFixed(2)}</p>
          <p><strong>Name:</strong> {stock.name}</p>
          <p><strong>Exchange:</strong> {stock.exchange}</p>
        </div>
      )}

      {news && news.length > 0 && (
        <div className="news-section">
          <h3>Recent News</h3>
          <ul>
            {news.slice(0, 5).map((item: any) => (
              <li key={item.id}>
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
                <small> - {item.source}</small>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showAnalysis && <AIAnalysisPanel ticker={ticker} />}
    </div>
  )
}
