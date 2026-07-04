import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import TraceButton from './TraceButton'

interface Asset {
  symbol: string
  name: string
  direction: 'bullish' | 'bearish' | 'neutral' | string
  impact_score: number
  rationale: string
  on_watchlist?: boolean
}
interface Result {
  title?: string | null
  summary: string
  overall: string
  assets: Asset[]
  usage_tokens?: number
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

function dirMeta(d: string) {
  return DIR[d as keyof typeof DIR] ?? DIR.neutral
}

export default function NewsAnalyzerModal({ onClose, onSelectTicker }: Props) {
  const qc = useQueryClient()
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [showText, setShowText] = useState(false)

  const analyze = useMutation<Result>({
    mutationFn: () =>
      apiClient
        .post('/news/analyze', { url: url.trim() || undefined, text: text.trim() || undefined })
        .then(r => r.data),
    onError: (e: any) => {
      // 422 = URL couldn't be fetched → reveal the paste-text fallback.
      if (e?.response?.status === 422) setShowText(true)
    },
  })

  const add = useMutation({
    mutationFn: (sym: string) => apiClient.post('/watchlist', { symbol: sym }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchlist'] })
      qc.invalidateQueries({ queryKey: ['movers'] })
      qc.invalidateQueries({ queryKey: ['candidates'] })
    },
  })

  const canAnalyze = (url.trim().length > 0 || text.trim().length > 0) && !analyze.isPending
  const result = analyze.data
  const errMsg = (analyze.error as any)?.response?.data?.detail

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal news-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h3>📰 News Analyser</h3>
          <button className="modal-close" onClick={onClose} title="Stäng">✕</button>
        </div>

        <div className="modal-body">
          <label className="nm-label">Länk till nyhet</label>
          <div className="nm-inputrow">
            <input
              className="nm-url"
              placeholder="https://…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && canAnalyze) analyze.mutate() }}
            />
            <TraceButton variant="green" onClick={() => analyze.mutate()} disabled={!canAnalyze}>
              {analyze.isPending ? <><span className="spinner" />Analyserar…</> : <>⬡ Analysera</>}
            </TraceButton>
          </div>

          {!showText ? (
            <button className="nm-toggle" onClick={() => setShowText(true)}>
              Betalvägg/JS-sida? Klistra in texten istället ▾
            </button>
          ) : (
            <div className="nm-textwrap">
              <label className="nm-label">Artikeltext (fallback)</label>
              <textarea
                className="nm-text"
                rows={6}
                placeholder="Klistra in artikeltexten här om URL:en inte kan läsas…"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          )}

          {analyze.isError && (
            <div className="nm-error">{errMsg || 'Analysen misslyckades — försök igen.'}</div>
          )}

          {analyze.isPending && (
            <div className="nm-loading"><span className="spinner" />Claude läser och analyserar nyheten…</div>
          )}

          {result && (
            <div className="nm-result">
              {result.title && <div className="nm-title">{result.title}</div>}

              <div className="nm-section-label">Sammanfattning</div>
              <p className="nm-summary">{result.summary}</p>

              {result.overall && (
                <>
                  <div className="nm-section-label">Marknadspåverkan</div>
                  <p className="nm-overall">{result.overall}</p>
                </>
              )}

              <div className="nm-section-label">Påverkade assets ({result.assets.length})</div>
              {result.assets.length === 0 ? (
                <p className="nm-empty">Inga specifika assets identifierades.</p>
              ) : (
                <div className="nm-assets">
                  {result.assets.map((a) => {
                    const dm = dirMeta(a.direction)
                    return (
                      <div className={`nm-asset ${dm.cls}`} key={a.symbol}>
                        <div className="nm-asset-top">
                          <button className="nm-asset-sym" title={`Visa detaljer för ${a.symbol}`}
                            onClick={() => onSelectTicker(a.symbol)}>
                            {a.symbol}
                          </button>
                          <span className={`nm-dir ${dm.cls}`}>{dm.arrow} {dm.label}</span>
                          <span className="nm-score" title={`Impact ${a.impact_score}/5`}>
                            {[1, 2, 3, 4, 5].map((n) => (
                              <span key={n} className={`nm-dot ${n <= a.impact_score ? 'on ' + dm.cls : ''}`} />
                            ))}
                          </span>
                          {a.on_watchlist ? (
                            <span className="nm-wl" title="I din watchlist">✓ WL</span>
                          ) : (
                            <button className="mv-add" title={`Lägg till ${a.symbol}`}
                              disabled={add.isPending && add.variables === a.symbol}
                              onClick={() => add.mutate(a.symbol)}>
                              {add.isPending && add.variables === a.symbol ? <span className="spinner" /> : '＋'}
                            </button>
                          )}
                        </div>
                        <div className="nm-asset-name">{a.name}</div>
                        <div className="nm-asset-why">{a.rationale}</div>
                      </div>
                    )
                  })}
                </div>
              )}

              <div className="nm-foot">
                {result.usage_tokens != null && <span>Tokens: {result.usage_tokens}</span>}
                <span className="nm-hint">AI-genererat · ej finansiell rådgivning</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
