import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface Point { t: string; price: number }
interface History { symbol: string; points: Point[]; prev_close?: number | null }

/** Minutes-of-day (Eastern) parsed straight from the ISO string's local time. */
function minutesET(iso: string): number | null {
  const m = iso.match(/T(\d{2}):(\d{2})/)
  return m ? parseInt(m[1], 10) * 60 + parseInt(m[2], 10) : null
}

const OPEN = 9 * 60 + 30   // 09:30 ET
const CLOSE = 16 * 60      // 16:00 ET

export default function PriceChart({ ticker }: { ticker: string }) {
  const { data, isLoading } = useQuery<History>({
    queryKey: ['history', ticker],
    queryFn: () => apiClient.get(`/stock/${ticker}/history`).then(r => r.data),
    enabled: !!ticker,
    refetchInterval: 60_000,
    staleTime: 55_000,
  })

  if (isLoading) return <div className="chart-empty"><span className="spinner" />Laddar graf…</div>
  const points = data?.points ?? []
  if (points.length < 2) return <div className="chart-empty">Ingen intradagsdata tillgänglig</div>

  const W = 600, H = 180, padY = 14
  const prevClose = data?.prev_close ?? null

  const prices = points.map(p => p.price)
  let min = Math.min(...prices)
  let max = Math.max(...prices)
  if (prevClose != null) { min = Math.min(min, prevClose); max = Math.max(max, prevClose) }
  const range = max - min || 1

  const n = points.length
  const x = (i: number) => (i / (n - 1)) * W
  const y = (v: number) => padY + (1 - (v - min) / range) * (H - 2 * padY)

  const linePts = points.map((p, i) => `${x(i).toFixed(1)},${y(p.price).toFixed(1)}`)
  const area = `M0,${H} L${linePts.join(' L')} L${W},${H} Z`

  const last = points[n - 1].price
  const up = prevClose != null ? last >= prevClose : last >= points[0].price
  const color = up ? 'var(--up)' : 'var(--down)'

  // Shade the pre-market and after-hours regions (outside 09:30–16:00 ET).
  const firstRegular = points.findIndex(p => { const m = minutesET(p.t); return m != null && m >= OPEN })
  const firstPost = points.findIndex(p => { const m = minutesET(p.t); return m != null && m >= CLOSE })
  const preWidth = firstRegular > 0 ? x(firstRegular) : 0
  const postX = firstPost > 0 ? x(firstPost) : W

  const chg = prevClose ? ((last - prevClose) / prevClose) * 100 : null

  return (
    <div className="price-chart-wrap">
      <svg className="price-chart" viewBox={`0 0 ${W} ${H}`} style={{ color }} preserveAspectRatio="none">
        <defs>
          <linearGradient id="pcFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.26" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>

        {preWidth > 0 && <rect x={0} y={0} width={preWidth} height={H} className="chart-session" />}
        {postX < W && <rect x={postX} y={0} width={W - postX} height={H} className="chart-session" />}

        {prevClose != null && (
          <line x1={0} x2={W} y1={y(prevClose)} y2={y(prevClose)} className="chart-prevclose" />
        )}

        <path d={area} fill="url(#pcFill)" stroke="none" />
        <polyline
          points={linePts.join(' ')}
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
        <circle cx={x(n - 1)} cy={y(last)} r={3.5} fill="currentColor" vectorEffect="non-scaling-stroke" />
      </svg>

      <div className="chart-legend">
        <span>Senast <b style={{ color }}>${last.toFixed(2)}</b>{chg != null && (
          <span style={{ color }}> ({chg >= 0 ? '+' : ''}{chg.toFixed(2)}%)</span>
        )}</span>
        {prevClose != null && <span>Prev close ${prevClose.toFixed(2)}</span>}
        <span>H ${max.toFixed(2)} · L ${min.toFixed(2)}</span>
        <span className="chart-hint">▚ = pre/efter-marknad</span>
      </div>
    </div>
  )
}
