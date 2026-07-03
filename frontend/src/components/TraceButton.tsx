import { useState, type CSSProperties, type ReactNode } from 'react'

export type TraceVariant = 'cyan' | 'green' | 'gold' | 'magenta' | 'orange' | 'violet'

/** base = dim static border, flash = the travelling light / glow color. */
const VARIANTS: Record<TraceVariant, { base: string; flash: string }> = {
  cyan: { base: '#0e7490', flash: '#22d3ee' },
  green: { base: '#0a6e4e', flash: '#00ff88' },
  gold: { base: '#b45309', flash: '#ffd700' },
  magenta: { base: '#8b1a4a', flash: '#ff2d95' },
  orange: { base: '#ff6b35', flash: '#ffb347' },
  violet: { base: '#7b2ff7', flash: '#c4b5fd' },
}

interface Props {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: TraceVariant
  direction?: 'cw' | 'ccw'
  /** Keep the light tracing even when not hovered (for primary/idle CTAs). */
  always?: boolean
  size?: 'sm' | 'md'
  type?: 'button' | 'submit'
  title?: string
  className?: string
}

export default function TraceButton({
  children,
  onClick,
  disabled = false,
  variant = 'cyan',
  direction = 'cw',
  always = false,
  size = 'md',
  type = 'button',
  title,
  className = '',
}: Props) {
  const [burst, setBurst] = useState(false)
  const { base, flash } = VARIANTS[variant]

  const handleClick = () => {
    if (disabled) return
    setBurst(true)
    setTimeout(() => setBurst(false), 420)
    onClick?.()
  }

  const style = {
    '--base-color': base,
    '--flash-color': flash,
  } as CSSProperties

  const rev = direction === 'ccw' ? ' reversed' : ''

  return (
    <button
      type={type}
      className={`trace-btn ${always ? 'trace-always ' : ''}trace-${size} ${className}`}
      style={style}
      onClick={handleClick}
      disabled={disabled}
      title={title}
    >
      <span className={`trace-light${rev}`} />
      <span className={`trace-outer-glow${rev}`} />
      <span className="trace-ambient" />
      <span className="trace-inner">{children}</span>
      {burst && <span className="burst" />}
    </button>
  )
}
