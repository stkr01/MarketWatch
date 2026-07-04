import { useEffect, useState } from 'react'

/**
 * Banner under the ticker tape: live wall-clock for each market, and in
 * parentheses either the countdown to the next open (when closed) or how long
 * it has already been open (when open). Regular-session hours, Mon–Fri.
 *
 * Note: countdowns use local wall-clock arithmetic, so on the two DST-switch
 * days a year the "time until open" can be off by an hour for a few hours.
 */
interface Market {
  city: string
  flag: string
  tz: string
  openMin: number   // minutes from local midnight
  closeMin: number
}

// Regular-session hours in each market's local time. (Tokyo has a 11:30–12:30
// lunch break we don't model — it just reads "open" straight through.)
const MARKETS: Market[] = [
  { city: 'Stockholm', flag: '🇸🇪', tz: 'Europe/Stockholm', openMin: 9 * 60, closeMin: 17 * 60 + 30 },
  { city: 'London', flag: '🇬🇧', tz: 'Europe/London', openMin: 8 * 60, closeMin: 16 * 60 + 30 },
  { city: 'New York', flag: '🇺🇸', tz: 'America/New_York', openMin: 9 * 60 + 30, closeMin: 16 * 60 },
  { city: 'Tokyo', flag: '🇯🇵', tz: 'Asia/Tokyo', openMin: 9 * 60, closeMin: 15 * 60 },
]

// Mon=0 … Sun=6
const WEEKDAY: Record<string, number> = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 }

function partsIn(tz: string, now: Date) {
  const p = new Intl.DateTimeFormat('en-GB', {
    timeZone: tz, hour12: false, weekday: 'short',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).formatToParts(now)
  const get = (t: string) => p.find(x => x.type === t)?.value ?? ''
  return {
    hour: parseInt(get('hour'), 10) % 24,   // some engines emit "24" at midnight
    minute: parseInt(get('minute'), 10),
    second: parseInt(get('second'), 10),
    day: WEEKDAY[get('weekday')] ?? 0,
  }
}

function fmtDur(totalSec: number): string {
  if (totalSec < 0) totalSec = 0
  const d = Math.floor(totalSec / 86400)
  const h = Math.floor((totalSec % 86400) / 3600)
  const m = Math.floor((totalSec % 3600) / 60)
  const s = Math.floor(totalSec % 60)
  if (d > 0) return `${d}d ${h}t`
  if (h > 0) return `${h}t ${String(m).padStart(2, '0')}m`
  return `${m}m ${String(s).padStart(2, '0')}s`
}

function computeState(m: Market, now: Date) {
  const { hour, minute, second, day } = partsIn(m.tz, now)
  const nowSec = hour * 3600 + minute * 60 + second
  const openSec = m.openMin * 60
  const closeSec = m.closeMin * 60
  const isWeekday = day <= 4
  const clock = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:${String(second).padStart(2, '0')}`

  if (isWeekday && nowSec >= openSec && nowSec < closeSec) {
    return { clock, open: true, note: `öppen ${fmtDur(nowSec - openSec)}` }
  }

  // Closed → seconds until the next session open.
  let untilSec: number
  if (isWeekday && nowSec < openSec) {
    untilSec = openSec - nowSec              // opens later today
  } else {
    let addDays = 1                          // start looking from tomorrow
    let probe = (day + 1) % 7
    while (probe > 4) { probe = (probe + 1) % 7; addDays++ }   // skip Sat/Sun
    untilSec = addDays * 86400 + openSec - nowSec
  }
  return { clock, open: false, note: `öppnar om ${fmtDur(untilSec)}` }
}

export default function MarketClocks() {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="market-clocks" aria-label="Market clocks and session countdowns">
      {MARKETS.map((m) => {
        const st = computeState(m, now)
        return (
          <div className="mkt-cell" key={m.city}>
            <span className={`mkt-dot ${st.open ? 'open' : 'closed'}`} />
            <span className="mkt-flag">{m.flag}</span>
            <span className="mkt-city">{m.city}</span>
            <span className="mkt-time">{st.clock}</span>
            <span className={`mkt-note ${st.open ? 'open' : 'closed'}`}>({st.note})</span>
          </div>
        )
      })}
    </div>
  )
}
