import { useState, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { priceSourceBadge } from '../utils'
import TraceButton from './TraceButton'

interface Alert {
  symbol: string
  gap_pct: number | null
  price_source: string | null
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

interface Props { onSelectTicker?: (sym: string) => void }

/** Compact alerts widget for the header — bell + count, click for a popover. */
export default function AlertsBell({ onSelectTicker }: Props) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testMsg, setTestMsg] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  const { data } = useQuery<Data>({
    queryKey: ['alerts'],
    queryFn: () => apiClient.get('/alerts').then(r => r.data),
    refetchInterval: 60 * 1000,
  })

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const count = data?.alerts.length ?? 0
  const active = !!data?.active

  const sendTest = async () => {
    setTesting(true); setTestMsg(null)
    try {
      const r = await apiClient.post('/alerts/test').then(res => res.data)
      setTestMsg(r.ok ? `Skickat via ${r.channels.join(', ')}` : r.detail)
      qc.invalidateQueries({ queryKey: ['alerts'] })
    } catch {
      setTestMsg('Testet misslyckades')
    } finally {
      setTesting(false)
    }
  }

  const pick = (sym: string) => { setOpen(false); onSelectTicker?.(sym) }

  return (
    <div className="alerts-bell" ref={ref}>
      <button
        className={`bell-btn ${active ? 'active' : ''}`}
        onClick={() => setOpen(o => !o)}
        title="Alerts"
        aria-label={`Alerts (${count})`}
      >
        🔔
        {count > 0 && <span className="bell-badge">{count > 99 ? '99+' : count}</span>}
        <span className={`bell-dot ${active ? 'on' : 'off'}`} />
      </button>

      {open && (
        <div className="bell-pop">
          <div className="bell-pop-head">
            <span>🔔 Alerts</span>
            {active && (
              <TraceButton variant="cyan" size="sm" onClick={sendTest} disabled={testing}>
                {testing ? <span className="spinner" /> : 'Test'}
              </TraceButton>
            )}
          </div>

          <div className={`bell-config ${active ? 'on' : 'off'}`}>
            {active ? (
              <>Aktiv · {data!.channels.join(', ')}<br />
                <span className="bell-config-sub">Triggar vid gap ≥ {data!.gap_threshold_pct}% &amp; RVOL ≥ {data!.rvol_threshold}</span>
              </>
            ) : (
              <>Inaktiv<br />
                <span className="bell-config-sub">Sätt TELEGRAM_BOT_TOKEN/CHAT_ID eller DISCORD_WEBHOOK_URL i .env</span>
              </>
            )}
          </div>
          {testMsg && <div className="bell-testmsg">{testMsg}</div>}

          {count === 0 ? (
            <div className="bell-empty">Inga alerts skickade än — triggar på starka kandidater (en gång per symbol/dag).</div>
          ) : (
            <div className="bell-list">
              {data!.alerts.slice(0, 12).map((a, i) => {
                const badge = priceSourceBadge(a.price_source)
                return (
                  <div className="bell-alert-row" key={`${a.symbol}-${a.sent_at}-${i}`}>
                    <button className="b-sym" onClick={() => pick(a.symbol)} title={`Visa ${a.symbol}`}>
                      {a.symbol}
                    </button>
                    <span style={{ color: gapColor(a.gap_pct), fontWeight: 600 }}>
                      {a.gap_pct == null ? '—' : `${a.gap_pct >= 0 ? '+' : ''}${a.gap_pct.toFixed(1)}%`}
                    </span>
                    {badge && <span className="src-badge" title={badge.title}>{badge.label}</span>}
                    <span className="bell-time">
                      {new Date(a.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
