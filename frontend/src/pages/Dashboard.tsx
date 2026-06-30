import { useState } from 'react'
import CandidateTable from '../components/CandidateTable'
import StockDetail from '../components/StockDetail'
import ScanStatusBar from '../components/ScanStatusBar'

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  return (
    <div className="app">
      <div className="dashboard">
        <div style={{ marginBottom: '2rem' }}>
          <h1>📈 Pre-Market Swing Trading Dashboard</h1>
          <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>
            Real-time candidate screening with Claude AI analysis
          </p>
        </div>

        <ScanStatusBar />

        <div className="dashboard-content">
          <div className="candidates-section">
            <h2>🎯 Current Candidates</h2>
            <CandidateTable onSelectTicker={setSelectedTicker} selectedTicker={selectedTicker} />
          </div>

          {selectedTicker && (
            <div className="detail-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2>📊 {selectedTicker}</h2>
                <button onClick={() => setSelectedTicker(null)} style={{ background: '#475569' }}>
                  Close
                </button>
              </div>
              <StockDetail ticker={selectedTicker} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
