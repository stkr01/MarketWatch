import { useState } from 'react'
import CandidateTable from '../components/CandidateTable'
import StockDetail from '../components/StockDetail'
import ScanStatusBar from '../components/ScanStatusBar'
import EconomicCalendar from '../components/EconomicCalendar'
import MarketClock from '../components/MarketClock'
import Watchlist from '../components/Watchlist'
import TickerTape from '../components/TickerTape'
import MarketClocks from '../components/MarketClocks'
import ScreenerPerformance from '../components/ScreenerPerformance'
import AlertsPanel from '../components/AlertsPanel'
import SettingsPanel from '../components/SettingsPanel'
import BriefingCard from '../components/BriefingCard'
import { yahooUrl } from '../utils'

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  return (
    <div className="dashboard">
      <TickerTape />
      <MarketClocks />

      <header className="app-header">
        <div>
          <h1 className="app-title">
            <span>📈</span>
            <span className="grad">Pre-Market Swing Dashboard</span>
          </h1>
          <p className="app-subtitle">
            Real-time candidate screening with Claude AI analysis
          </p>
        </div>
        <MarketClock />
      </header>

      <ScanStatusBar />

      <BriefingCard />

      <div className="content-grid">
        <main className="panel">
          <div className="panel-header">
            <div className="panel-title">🎯 Current Candidates</div>
          </div>
          <div className="panel-body">
            <CandidateTable onSelectTicker={setSelectedTicker} selectedTicker={selectedTicker} />
          </div>
        </main>

        <aside>
          <Watchlist />
          <SettingsPanel />
          <AlertsPanel />
          <ScreenerPerformance />
          <EconomicCalendar />
        </aside>
      </div>

      {selectedTicker && (
        <div className="panel fade-in" style={{ marginTop: '1.5rem' }}>
          <div className="panel-header">
            <div className="panel-title">
              📊
              <a
                className="ticker-link"
                href={yahooUrl(selectedTicker)}
                target="_blank"
                rel="noopener noreferrer"
              >
                {selectedTicker}<span className="ext">↗</span>
              </a>
            </div>
            <button className="btn-ghost btn-sm" onClick={() => setSelectedTicker(null)}>
              ✕ Close
            </button>
          </div>
          <div className="panel-pad">
            <StockDetail ticker={selectedTicker} />
          </div>
        </div>
      )}
    </div>
  )
}
