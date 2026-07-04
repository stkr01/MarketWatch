interface Props {
  data?: number[]
  width?: number
  height?: number
  /** Direction reference (e.g. prior close). Falls back to the first point. */
  baseline?: number | null
}

/** Tiny inline-SVG sparkline, green/red by direction. No dependencies. */
export default function Sparkline({ data, width = 90, height = 26, baseline }: Props) {
  if (!data || data.length < 2) return <span className="spark-empty">—</span>

  const padY = 3
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const stepX = width / (data.length - 1)
  const y = (v: number) => padY + (1 - (v - min) / range) * (height - 2 * padY)

  const pts = data.map((v, i) => `${(i * stepX).toFixed(1)},${y(v).toFixed(1)}`)
  const line = pts.join(' ')
  const area = `M0,${height} L${pts.join(' L')} L${width},${height} Z`

  const ref = baseline ?? data[0]
  const up = data[data.length - 1] >= ref
  const color = up ? 'var(--up)' : 'var(--down)'

  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      style={{ color }}
      role="img"
      aria-label={up ? 'up trend' : 'down trend'}
    >
      <path d={area} fill="currentColor" opacity={0.12} />
      <polyline
        points={line}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}
