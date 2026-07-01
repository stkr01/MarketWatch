import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

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

export default function BriefingCard() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery<Briefing>({
    queryKey: ['briefing'],
    queryFn: () => apiClient.get('/briefing').then(r => r.data),
  })

  const generate = useMutation({
    mutationFn: () => apiClient.post('/briefing/generate').then(r => r.data),
    onSuccess: (b: Briefing) => qc.setQueryData(['briefing'], b),
  })

  const hasContent = !!data?.content
  const busy = generate.isPending

  return (
    <div className="panel briefing" style={{ marginBottom: '1.75rem' }}>
      <div className="panel-header">
        <div className="panel-title">🌅 Morning Briefing</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {data?.generated_at && (
            <span className="briefing-time">
              {new Date(data.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              {data.usage_tokens ? ` · ${data.usage_tokens} tok` : ''}
            </span>
          )}
          <button
            className={hasContent ? 'btn-ghost btn-sm' : ''}
            onClick={() => generate.mutate()}
            disabled={busy}
          >
            {busy ? <><span className="spinner" />Generating…</> : hasContent ? '↻ Refresh' : '✨ Generate'}
          </button>
        </div>
      </div>

      <div className="panel-pad">
        {isLoading ? (
          <div className="loading"><span className="spinner" />Loading…</div>
        ) : generate.isError ? (
          <div className="wl-error">Could not generate briefing. Check the API key and try again.</div>
        ) : hasContent ? (
          <div className="briefing-body">{renderContent(data!.content!)}</div>
        ) : (
          <div className="briefing-empty">
            <p>Get an AI-generated summary of today's candidates and economic calendar.</p>
            <small>Uses Claude · one briefing cached per day (refresh anytime)</small>
          </div>
        )}
      </div>
    </div>
  )
}
