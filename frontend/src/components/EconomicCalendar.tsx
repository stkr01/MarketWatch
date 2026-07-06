import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface EconEvent {
  time: string
  datetime: string
  title: string
  impact: string
  forecast: string
  previous: string
  is_upcoming: boolean
}

function impactClass(impact: string): string {
  const key = impact.toLowerCase()
  if (key === 'high') return 'impact-high'
  if (key === 'medium') return 'impact-medium'
  if (key === 'holiday') return 'impact-holiday'
  return 'impact-low'
}

// Time left until `iso` (which carries the event's ET offset). Computed against
// the viewer's own clock, so it's timezone-agnostic — no ET↔local juggling.
function formatCountdown(iso: string, now: number): string | null {
  const target = new Date(iso).getTime()
  if (isNaN(target)) return null
  const diff = Math.round((target - now) / 1000) // seconds
  if (diff <= 0) return 'nu'
  if (diff < 60) return `om ${diff}s`
  const mins = Math.floor(diff / 60)
  if (mins < 60) return `om ${mins}m`
  const hours = Math.floor(mins / 60)
  const remMin = mins % 60
  return remMin ? `om ${hours}h ${remMin}m` : `om ${hours}h`
}

export default function EconomicCalendar() {
  const { data: events = [], isLoading, error } = useQuery<EconEvent[]>({
    queryKey: ['economic-calendar'],
    queryFn: () => apiClient.get('/economic-calendar').then(r => r.data),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    staleTime: 60 * 1000,
  })

  // Tick every second so the countdowns stay live.
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const upcomingCount = events.filter(e => e.is_upcoming).length
  const nextIdx = events.findIndex(e => e.is_upcoming)

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          🗓️ US Economic Calendar
          {upcomingCount > 0 && <span className="count">{upcomingCount} upcoming</span>}
        </div>
      </div>

      {isLoading ? (
        <div className="loading"><span className="spinner" />Loading events…</div>
      ) : error ? (
        <div className="empty">Could not load calendar</div>
      ) : events.length === 0 ? (
        <div className="empty">
          No US economic events scheduled today
          <small>Weekends and holidays have no releases</small>
        </div>
      ) : (
        <div className="econ-list">
          {events.map((e, i) => {
            const secsLeft = (new Date(e.datetime).getTime() - now) / 1000
            const countdown = e.is_upcoming ? formatCountdown(e.datetime, now) : null
            return (
            <div
              key={`${e.datetime}-${e.title}`}
              className={`econ-item ${!e.is_upcoming ? 'past' : ''} ${i === nextIdx ? 'next' : ''}`}
            >
              <div className="econ-time">
                {e.time}
                {countdown && (
                  <div className={`econ-countdown ${secsLeft <= 900 ? 'soon' : ''}`}>{countdown}</div>
                )}
              </div>
              <div>
                <div className="econ-title">{e.title}</div>
                {(e.forecast || e.previous) && (
                  <div className="econ-sub">
                    {e.forecast && <>Forecast <b>{e.forecast}</b></>}
                    {e.forecast && e.previous && ' · '}
                    {e.previous && <>Prev {e.previous}</>}
                  </div>
                )}
              </div>
              <span className={`impact ${impactClass(e.impact)}`}>
                <span className="dot" />
                {e.impact}
              </span>
            </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
