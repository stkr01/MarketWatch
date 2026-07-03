import { type CSSProperties, type ReactNode } from 'react'

export type StatusTone = 'green' | 'orange' | 'red' | 'cyan' | 'dim'

const TONE_COLOR: Record<StatusTone, string> = {
  green: '#00e676',
  orange: '#ffab00',
  red: '#ff1744',
  cyan: '#22d3ee',
  dim: '#64748b',
}

interface Props {
  tone: StatusTone
  title: ReactNode
  children?: ReactNode
  /** Compact inline chip instead of the full boxed banner. */
  chip?: boolean
  className?: string
}

export default function StatusBox({ tone, title, children, chip = false, className = '' }: Props) {
  const style = { '--status-color': TONE_COLOR[tone] } as CSSProperties

  if (chip) {
    return (
      <span className={`status-chip status-${tone} ${className}`} style={style}>
        <span className="status-dot" />
        {title}
      </span>
    )
  }

  return (
    <div className={`status-box status-${tone} ${className}`} style={style}>
      <span className="status-box-glow" />
      <p className="status-title"><span className="status-dot" />{title}</p>
      {children && <p className="status-desc">{children}</p>}
    </div>
  )
}
