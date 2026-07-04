import { useState, useRef, useEffect } from 'react'
import CandidateTable from '../components/CandidateTable'
import StockDetail from '../components/StockDetail'
import ScanStatusBar from '../components/ScanStatusBar'
import EconomicCalendar from '../components/EconomicCalendar'
import MarketClock from '../components/MarketClock'
import Watchlist from '../components/Watchlist'
import MarketMovers from '../components/MarketMovers'
import TickerTape from '../components/TickerTape'
import MarketClocks from '../components/MarketClocks'
import ScreenerPerformance from '../components/ScreenerPerformance'
import AlertsPanel from '../components/AlertsPanel'
import SettingsPanel from '../components/SettingsPanel'
import BriefingCard from '../components/BriefingCard'
import ActionBar from '../components/ActionBar'
import NewsAnalyzerModal from '../components/NewsAnalyzerModal'
import { yahooUrl } from '../utils'

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)
  const [newsOpen, setNewsOpen] = useState(false)
  const detailRef = useRef<HTMLDivElement>(null)

  // Selecting a ticker anywhere opens the in-app detail panel and scrolls to it.
  const selectTicker = (sym: string) => setSelectedTicker(sym.toUpperCase())

  useEffect(() => {
    if (selectedTicker) {
      detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [selectedTicker])

  return (
    <div className="dashboard">
      <TickerTape />
      <MarketClocks />

      <header className="app-header">
        <div>
          <h1 className="app-title">
            <span>📈</span>
            <span className="grad">Krantz Pre-Market AI Dashboard</span>
          </h1>
          <p className="app-subtitle">
            Real-time candidate screening with Claude AI analysis
          </p>
        </div>
        <MarketClock />
      </header>

      <ActionBar onOpenNews={() => setNewsOpen(true)} />

      <ScanStatusBar />

      <BriefingCard />

      <div className="content-grid">
        <main className="panel">
          <div className="panel-header">
            <div className="panel-title">🎯 Current Candidates</div>
          </div>
          <div className="panel-body">
            <CandidateTable onSelectTicker={selectTicker} selectedTicker={selectedTicker} />
          </div>
        </main>

        <aside>
          <Watchlist onSelectTicker={selectTicker} />
          <MarketMovers onSelectTicker={selectTicker} />
          <SettingsPanel />
          <AlertsPanel />
          <ScreenerPerformance />
          <EconomicCalendar />
        </aside>
      </div>

      {selectedTicker && (
        <div className="panel fade-in" ref={detailRef} style={{ marginTop: '1.5rem' }}>
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

      {newsOpen && (
        <NewsAnalyzerModal
          onClose={() => setNewsOpen(false)}
          onSelectTicker={(sym) => { setNewsOpen(false); selectTicker(sym) }}
        />
      )}
    </div>
  )
}
