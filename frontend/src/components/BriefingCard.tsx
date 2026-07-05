import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import TraceButton from './TraceButton'

interface Briefing {
  date: string
  content: string | null
  generated_at: string | null
  usage_tokens: number | null
}

/** Minimal renderer: # headings, **bold**, line breaks — no markdown dep. */
function renderContent(text: string) {
  return text.split('\n').map((line, i) => {
    if (!line.trim()) return <div key={i} style={{ height: '0.6rem' }} />

    const heading = line.match(/^(#+)\s+(.*)$/)
    if (heading) {
      return <div key={i} className="briefing-h">{heading[2]}</div>
    }

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

// Format: "2026-05-05 Kl14:04"
function fmtBriefingStamp(dateStr: string, iso?: string | null) {
  if (!iso) return dateStr
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z')
  return `${dateStr} Kl${d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })}`
}

export default function BriefingCard() {
  const qc = useQueryClient()
  const [showHistory, setShowHistory] = useState(false)
  const [openDate, setOpenDate] = useState<string | null>(null)

  const { data, isLoading } = useQuery<Briefing>({
    queryKey: ['briefing'],
    queryFn: () => apiClient.get('/briefing').then(r => r.data),
  })

  const history = useQuery<Briefing[]>({
    queryKey: ['briefing-history'],
    queryFn: () => apiClient.get('/briefing/history').then(r => r.data),
    enabled: showHistory,
  })

  const generate = useMutation({
    mutationFn: () => apiClient.post('/briefing/generate').then(r => r.data),
    onSuccess: (b: Briefing) => {
      qc.setQueryData(['briefing'], b)
      qc.invalidateQueries({ queryKey: ['briefing-history'] })
    },
  })

  const hasContent = !!data?.content
  const busy = generate.isPending

  // History excludes today (already shown above).
  const pastBriefings = (history.data ?? []).filter(b => b.date !== data?.date && b.content)

  return (
    <div className="panel briefing" style={{ marginBottom: '1.75rem' }}>
      <div className="panel-header">
        <div className="panel-title">🌅 Morgonbriefing</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {data?.generated_at && (
            <span className="briefing-time">
              {new Date(data.generated_at).toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })}
              {data.usage_tokens ? ` · ${data.usage_tokens} tok` : ''}
            </span>
          )}
          <button
            className={`briefing-hist-toggle ${showHistory ? 'active' : ''}`}
            onClick={() => setShowHistory(v => !v)}
            title="Visa tidigare briefingar"
          >
            🕐 Historik
          </button>
          <TraceButton variant="gold" size="sm" always={!hasContent} onClick={() => generate.mutate()} disabled={busy}>
            {busy ? <><span className="spinner" />Genererar…</> : hasContent ? '↻ Uppdatera' : '✦ Generera'}
          </TraceButton>
        </div>
      </div>

      <div className="panel-pad">
        {isLoading ? (
          <div className="loading"><span className="spinner" />Laddar…</div>
        ) : generate.isError ? (
          <div className="wl-error">Kunde inte generera briefingen. Kontrollera API-nyckeln och försök igen.</div>
        ) : hasContent ? (
          <div className="briefing-body">{renderContent(data!.content!)}</div>
        ) : (
          <div className="briefing-empty">
            <p>Få en AI-genererad sammanfattning av dagens kandidater och ekonomiska kalender.</p>
            <small>Drivs av Claude · en briefing sparas per dag (uppdatera när du vill)</small>
          </div>
        )}

        {showHistory && (
          <div className="briefing-history">
            <div className="briefing-history-head">Tidigare briefingar</div>
            {history.isLoading ? (
              <div className="loading"><span className="spinner" />Laddar historik…</div>
            ) : pastBriefings.length === 0 ? (
              <p className="briefing-empty"><small>Inga tidigare briefingar sparade ännu.</small></p>
            ) : (
              <div className="briefing-hist-list">
                {pastBriefings.map((b) => {
                  const open = openDate === b.date
                  return (
                    <div className="briefing-hist-item" key={b.date}>
                      <button
                        className="briefing-hist-row"
                        onClick={() => setOpenDate(open ? null : b.date)}
                      >
                        <span className="briefing-hist-date">{fmtBriefingStamp(b.date, b.generated_at)}</span>
                        <span className="briefing-hist-meta">
                          {b.usage_tokens ? `${b.usage_tokens} tok` : ''}
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
            )}
          </div>
        )}
      </div>
    </div>
  )
}
