import { useState } from 'react'
import CandidateTable from '../components/CandidateTable'
import StockDetail from '../components/StockDetail'
import ScanStatusBar from '../components/ScanStatusBar'

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  return (
    <div className="dashboard">
      <h1>Pre-Market Swing Trading Dashboard</h1>

      <ScanStatusBar />

      <div className="dashboard-content">
        <div className="candidates-section">
          <h2>Candidates</h2>
          <CandidateTable onSelectTicker={setSelectedTicker} />
        </div>

        {selectedTicker && (
          <div className="detail-section">
            <StockDetail ticker={selectedTicker} />
          </div>
        )}
      </div>
    </div>
  )
}
