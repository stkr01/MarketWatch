import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface BriefingItem {
  date: string
  content: string | null
  generated_at: string | null
  usage_tokens: number | null
}
interface NewsListItem {
  id: number
  title?: string | null
  source_url?: string | null
  summary: string
  impact_max: number
  asset_count: number
  created_at: string
}
interface Asset {
  symbol: string
  name: string
  direction: string
  impact_score: number
  rationale: string
  on_watchlist?: boolean
}
interface NewsDetail {
  id: number
  title?: string | null
  source_url?: string | null
  summary: string
  overall: string
  assets: Asset[]
  usage_tokens?: number
  created_at: string
}

interface Props {
  onClose: () => void
  onSelectTicker: (sym: string) => void
}

const DIR = {
  bullish: { arrow: '▲', cls: 'bull', label: 'Bullish' },
  bearish: { arrow: '▼', cls: 'bear', label: 'Bearish' },
  neutral: { arrow: '■', cls: 'neut', label: 'Neutral' },
} as const
const dirMeta = (d: string) => DIR[d as keyof typeof DIR] ?? DIR.neutral

function fmtDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z')
  return d.toLocaleString('sv-SE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}
function fmtDay(dateStr: string) {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('sv-SE', { weekday: 'short', day: 'numeric', month: 'short' })
}

/** Minimal markdown-ish renderer: # headings, **bold**, line breaks. */
function renderContent(text: string) {
  return text.split('\n').map((line, i) => {
    if (!line.trim()) return <div key={i} style={{ height: '0.6rem' }} />
    const heading = line.match(/^(#+)\s+(.*)$/)
    if (heading) return <div key={i} className="briefing-h">{heading[2]}</div>
    return (
      <div key={i}>
        {line.split(/(\*\*[^*]+\*\*)/g).map((part, j) =>
          part.startsWith('**') && part.endsWith('**')
            ? <strong key={j}>{part.slice(2, -2)}</strong>
            : <span key={j}>{part}</span>
        )}
      </div>
    )
  })
}

export default function HistoryModal({ onClose, onSelectTicker }: Props) {
  const [tab, setTab] = useState<'briefing' | 'news'>('briefing')
  const [openDate, setOpenDate] = useState<string | null>(null)
  const [newsId, setNewsId] = useState<number | null>(null)

  const briefings = useQuery<BriefingItem[]>({
    queryKey: ['briefing-history'],
    queryFn: () => apiClient.get('/briefing/history').then(r => r.data),
    enabled: tab === 'briefing',
  })

  const news = useQuery<NewsListItem[]>({
    queryKey: ['news-history'],
    queryFn: () => apiClient.get('/news/analyze/history').then(r => r.data),
    enabled: tab === 'news',
  })

  const newsItem = useQuery<NewsDetail>({
    queryKey: ['news-history', newsId],
    queryFn: () => apiClient.get(`/news/analyze/history/${newsId}`).then(r => r.data),
    enabled: newsId != null,
  })

  const briefingRows = (briefings.data ?? []).filter(b => b.content)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal news-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>🕐 Historik</h3>
          <div className="nm-tabs">
            <button className={`nm-tab ${tab === 'briefing' ? 'active' : ''}`}
              onClick={() => setTab('briefing')}>🌅 Morgonbriefing</button>
            <button className={`nm-tab ${tab === 'news' ? 'active' : ''}`}
              onClick={() => { setTab('news'); setNewsId(null) }}>📰 News Analyser</button>
          </div>
          <button className="modal-close" onClick={onClose} title="Stäng">✕</button>
        </div>

        <div className="modal-body">
          {tab === 'briefing' ? (
            briefings.isLoading ? (
              <div className="nm-loading"><span className="spinner" />Laddar historik…</div>
            ) : briefingRows.length === 0 ? (
              <p className="nm-empty">Inga sparade briefingar ännu.</p>
            ) : (
              <div className="briefing-hist-list">
                {briefingRows.map((b) => {
                  const open = openDate === b.date
                  return (
                    <div className="briefing-hist-item" key={b.date}>
                      <button className="briefing-hist-row" onClick={() => setOpenDate(open ? null : b.date)}>
                        <span className="briefing-hist-date">{fmtDay(b.date)}</span>
                        <span className="briefing-hist-meta">
                          {b.generated_at && new Date(b.generated_at).toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })}
                          {b.usage_tokens ? ` · ${b.usage_tokens} tok` : ''}
                        </span>
                        <span className="briefing-hist-caret">{open ? '▾' : '▸'}</span>
                      </button>
                      {open && b.content && (
                        <div className="briefing-body briefing-hist-body">{renderContent(b.content)}</div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          ) : newsId != null ? (
            <>
              <button className="nm-back" onClick={() => setNewsId(null)}>← Tillbaka till historik</button>
              {newsItem.isLoading && <div className="nm-loading"><span className="spinner" />Laddar analys…</div>}
              {newsItem.data && (
                <div className="nm-result">
                  {newsItem.data.title && <div className="nm-title">{newsItem.data.title}</div>}
                  <div className="nm-meta">
                    <span>🕐 {fmtDate(newsItem.data.created_at)}</span>
                    {newsItem.data.source_url && (
                      <a href={newsItem.data.source_url} target="_blank" rel="noopener noreferrer" className="nm-src">🔗 Källa</a>
                    )}
                  </div>
                  <div className="nm-section-label">Sammanfattning</div>
                  <p className="nm-summary">{newsItem.data.summary}</p>
                  {newsItem.data.overall && (
                    <>
                      <div className="nm-section-label">Marknadspåverkan</div>
                      <p className="nm-overall">{newsItem.data.overall}</p>
                    </>
                  )}
                  <div className="nm-section-label">Påverkade assets ({newsItem.data.assets.length})</div>
                  {newsItem.data.assets.length === 0 ? (
                    <p className="nm-empty">Inga specifika assets identifierades.</p>
                  ) : (
                    <div className="nm-assets">
                      {newsItem.data.assets.map((a) => {
                        const dm = dirMeta(a.direction)
                        return (
                          <div className={`nm-asset ${dm.cls}`} key={a.symbol}>
                            <div className="nm-asset-top">
                              <button className="nm-asset-sym" title={`Visa detaljer för ${a.symbol}`}
                                onClick={() => { onSelectTicker(a.symbol); onClose() }}>{a.symbol}</button>
                              <span className={`nm-dir ${dm.cls}`}>{dm.arrow} {dm.label}</span>
                              <span className="nm-score" title={`Impact ${a.impact_score}/5`}>
                                {[1, 2, 3, 4, 5].map((n) => (
                                  <span key={n} className={`nm-dot ${n <= a.impact_score ? 'on ' + dm.cls : ''}`} />
                                ))}
                              </span>
                              {a.on_watchlist && <span className="nm-wl" title="I din watchlist">✓ WL</span>}
                            </div>
                            <div className="nm-asset-name">{a.name}</div>
                            <div className="nm-asset-why">{a.rationale}</div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : news.isLoading ? (
            <div className="nm-loading"><span className="spinner" />Laddar historik…</div>
          ) : (news.data ?? []).length === 0 ? (
            <p className="nm-empty">Inga sparade analyser ännu.</p>
          ) : (
            <div className="nm-hist">
              {news.data!.map((h) => (
                <div className="nm-hist-item" key={h.id} onClick={() => setNewsId(h.id)}>
                  <div className="nm-hist-main">
                    <div className="nm-hist-title">{h.title || h.summary.slice(0, 80) || 'Analys'}</div>
                    <div className="nm-hist-sub">
                      <span>🕐 {fmtDate(h.created_at)}</span>
                      <span>· {h.asset_count} assets</span>
                      {h.impact_max > 0 && <span className="nm-hist-impact">· max {h.impact_max}/5</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
