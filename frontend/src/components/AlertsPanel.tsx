import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { yahooUrl, priceSourceBadge } from '../utils'

interface Alert {
  symbol: string
  gap_pct: number | null
  rvol: number | null
  price: number | null
  price_source: string | null
  channels: string | null
  status: string
  sent_at: string
}
interface Data {
  enabled: boolean
  active: boolean
  channels: string[]
  gap_threshold_pct: number
  rvol_threshold: number
  alerts: Alert[]
}

const gapColor = (v: number | null) =>
  v == null ? 'var(--text)' : v >= 0 ? 'var(--up)' : 'var(--down)'

export default function AlertsPanel() {
  const qc = useQueryClient()
  const [testing, setTesting] = useState(false)
  const [testMsg, setTestMsg] = useState<string | null>(null)

  const { data, isLoading } = useQuery<Data>({
    queryKey: ['alerts'],
    queryFn: () => apiClient.get('/alerts').then(r => r.data),
    refetchInterval: 60 * 1000,
  })

  const sendTest = async () => {
    setTesting(true)
    setTestMsg(null)
    try {
      const r = await apiClient.post('/alerts/test').then(res => res.data)
      setTestMsg(r.ok ? `Sent via ${r.channels.join(', ')}` : r.detail)
      qc.invalidateQueries({ queryKey: ['alerts'] })
    } catch {
      setTestMsg('Test failed')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="panel" style={{ marginBottom: '1.5rem' }}>
      <div className="panel-header">
        <div className="panel-title">
          🔔 Alerts
          {data && data.alerts.length > 0 && <span className="count">{data.alerts.length}</span>}
        </div>
        {data?.active && (
          <button className="btn-ghost btn-sm" onClick={sendTest} disabled={testing}>
            {testing ? <span className="spinner" /> : 'Test'}
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="loading" style={{ padding: '1.25rem' }}><span className="spinner" />Loading…</div>
      ) : !data ? null : (
        <>
          <div className="alert-config">
            {data.active ? (
              <span className="alert-on">
                ● Active · {data.channels.join(', ')} · gap ≥ {data.gap_threshold_pct}% & RVOL ≥ {data.rvol_threshold}
              </span>
            ) : (
              <span className="alert-off">
                ○ Inactive — set TELEGRAM_BOT_TOKEN/CHAT_ID or DISCORD_WEBHOOK_URL in backend/.env
              </span>
            )}
            {testMsg && <div className="alert-testmsg">{testMsg}</div>}
          </div>

          {data.alerts.length === 0 ? (
            <div className="empty" style={{ padding: '1rem 1.25rem' }}>
              No alerts sent yet
              <small>Fires on strong candidates (once per symbol/day)</small>
            </div>
          ) : (
            <div className="alert-list">
              {data.alerts.slice(0, 10).map((a, i) => {
                const badge = priceSourceBadge(a.price_source)
                return (
                  <div className="alert-row" key={`${a.symbol}-${a.sent_at}-${i}`}>
                    <a className="ticker-link" href={yahooUrl(a.symbol)} target="_blank" rel="noopener noreferrer">
                      {a.symbol}
                    </a>
                    <span className="alert-gap" style={{ color: gapColor(a.gap_pct) }}>
                      {a.gap_pct == null ? '—' : `${a.gap_pct >= 0 ? '+' : ''}${a.gap_pct.toFixed(1)}%`}
                    </span>
                    {badge && <span className="src-badge" title={badge.title}>{badge.label}</span>}
                    {a.status !== 'sent' && <span className="alert-status">{a.status}</span>}
                    <span className="alert-time">
                      {new Date(a.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
