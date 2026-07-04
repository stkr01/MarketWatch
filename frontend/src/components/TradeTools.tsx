import { useMutation } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import TraceButton from './TraceButton'

interface Plan {
  direction: 'long' | 'short'
  entry: number
  stop: number
  target: number
  risk: number
  reward: number
  rr: number | null
  atr_used: number
  plan: string
  usage_tokens?: number
}

function errText(e: any): string {
  return e?.response?.data?.detail || 'Något gick fel — försök igen.'
}

export default function TradeTools({ ticker }: { ticker: string }) {
  const why = useMutation<{ response: string; usage_tokens?: number }>({
    mutationFn: () => apiClient.post(`/stock/${ticker}/why`).then(r => r.data),
  })
  const plan = useMutation<Plan>({
    mutationFn: () => apiClient.post(`/stock/${ticker}/trade-plan`).then(r => r.data),
  })

  return (
    <div className="trade-tools">
      {/* Why is it gapping? */}
      <div className="tt-block">
        <div className="tt-head">
          <span className="tt-title">❓ Varför gappar den?</span>
          {why.isSuccess && (
            <TraceButton variant="cyan" size="sm" onClick={() => why.mutate()}>↻ Uppdatera</TraceButton>
          )}
        </div>
        {!why.data && !why.isPending && !why.isError && (
          <TraceButton variant="cyan" always onClick={() => why.mutate()}>⬡ Förklara gapet</TraceButton>
        )}
        {why.isPending && <div className="tt-loading"><span className="spinner" />Claude tänker…</div>}
        {why.isError && <div className="tt-error">{errText(why.error)} <TraceButton variant="magenta" size="sm" onClick={() => why.mutate()}>Försök igen</TraceButton></div>}
        {why.data && <div className="tt-text">{why.data.response}</div>}
      </div>

      {/* Trade plan */}
      <div className="tt-block">
        <div className="tt-head">
          <span className="tt-title">🎯 Trade-plan</span>
          {plan.isSuccess && (
            <TraceButton variant="green" size="sm" onClick={() => plan.mutate()}>↻ Uppdatera</TraceButton>
          )}
        </div>
        {!plan.data && !plan.isPending && !plan.isError && (
          <TraceButton variant="green" always onClick={() => plan.mutate()}>⬡ Generera trade-plan</TraceButton>
        )}
        {plan.isPending && <div className="tt-loading"><span className="spinner" />Bygger plan…</div>}
        {plan.isError && <div className="tt-error">{errText(plan.error)} <TraceButton variant="magenta" size="sm" onClick={() => plan.mutate()}>Försök igen</TraceButton></div>}
        {plan.data && (
          <>
            <div className="tt-levels">
              <span className={`tt-dir ${plan.data.direction}`}>
                {plan.data.direction === 'long' ? '▲ LONG' : '▼ SHORT'}
              </span>
              <div className="tt-level"><span>Entry</span><b>${plan.data.entry.toFixed(2)}</b></div>
              <div className="tt-level stop"><span>Stop</span><b>${plan.data.stop.toFixed(2)}</b></div>
              <div className="tt-level target"><span>Target</span><b>${plan.data.target.toFixed(2)}</b></div>
              <div className="tt-level"><span>R:R</span><b>{plan.data.rr != null ? `${plan.data.rr.toFixed(1)}R` : '—'}</b></div>
              <div className="tt-level"><span>ATR</span><b>${plan.data.atr_used.toFixed(2)}</b></div>
            </div>
            <div className="tt-text">{plan.data.plan}</div>
            <div className="tt-note">Nivåer beräknade från ATR (stop 1× ATR, target 2× ATR). Ej finansiell rådgivning.</div>
          </>
        )}
      </div>
    </div>
  )
}
