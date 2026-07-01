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

export default function EconomicCalendar() {
  const { data: events = [], isLoading, error } = useQuery<EconEvent[]>({
    queryKey: ['economic-calendar'],
    queryFn: () => apiClient.get('/economic-calendar').then(r => r.data),
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    staleTime: 60 * 1000,
  })

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
          {events.map((e, i) => (
            <div
              key={`${e.datetime}-${e.title}`}
              className={`econ-item ${!e.is_upcoming ? 'past' : ''} ${i === nextIdx ? 'next' : ''}`}
            >
              <div className="econ-time">{e.time}</div>
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
          ))}
        </div>
      )}
    </div>
  )
}
