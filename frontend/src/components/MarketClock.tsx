import { useEffect, useState } from 'react'
import { marketSession } from '../utils'

export default function MarketClock() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const time = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(now)

  const date = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  }).format(now)

  const session = marketSession(now)

  return (
    <div className="market-clock">
      <div className="clock-main">
        <div className="clock-time">{time}</div>
        <div className="clock-zone">{date} · ET</div>
      </div>
      <span className={`session-pill ${session.cls}`}>
        <span className="dot" />
        {session.label}
      </span>
    </div>
  )
}
