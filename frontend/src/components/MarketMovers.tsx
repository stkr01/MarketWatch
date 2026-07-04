import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { yahooUrl } from '../utils'

interface Mover {
  symbol: string
  name: string
  price: number | null
  change_pct: number | null
  rvol: number | null
  volume: number | null
  market_cap: number | null
  session: string
  source: string
  on_watchlist: boolean
}

const SRC_LABEL: Record<string, string> = {
  gainer: '▲ Gainer', loser: '▼ Loser', active: '⚡ Active', 'small-cap': 'SC',
}

export default function MarketMovers() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery<{ as_of: string | null; movers: Mover[] }>({
    queryKey: ['movers'],
    queryFn: () => apiClient.get('/movers').then(r => r.data),
    refetchInterval: 120_000,
  })

  const add = useMutation({
    mutationFn: (sym: string) => apiClient.post('/watchlist', { symbol: sym }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchlist'] })
      qc.invalidateQueries({ queryKey: ['movers'] })
      qc.invalidateQueries({ queryKey: ['candidates'] })
    },
  })

  const movers = data?.movers ?? []

  return (
    <div className="panel" style={{ marginBottom: '1.5rem' }}>
      <div className="panel-header">
        <div className="panel-title">
          🔥 Market Movers
          {movers.length > 0 && <span className="count">{movers.length}</span>}
        </div>
      </div>

      <div className="panel-pad">
        <p style={{ color: 'var(--text-dim)', fontSize: '0.78rem', marginTop: 0, marginBottom: '0.75rem' }}>
          Auto-upptäckta rörare (Yahoo-screeners). Tryck ＋ för att lägga till i watchlist.
        </p>

        {isLoading ? (
          <div className="loading" style={{ padding: '1rem' }}><span className="spinner" />Söker rörare…</div>
        ) : movers.length === 0 ? (
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>Inga rörare hittades just nu.</p>
        ) : (
          <div className="mv-list">
            {movers.map((m) => {
              const up = (m.change_pct ?? 0) >= 0
              return (
                <div className="mv-row" key={m.symbol}>
                  <div className="mv-main">
                    <a className="mv-sym" href={yahooUrl(m.symbol)} target="_blank" rel="noopener noreferrer" title={m.name}>
                      {m.symbol}<span className="ext">↗</span>
                    </a>
                    <span className="mv-src" title={`Källa: ${m.source} · ${m.session}`}>{SRC_LABEL[m.source] ?? m.source}</span>
                  </div>
                  <span className={`pill ${up ? 'pill-up' : 'pill-down'}`}>
                    {up ? '▲' : '▼'} {up ? '+' : ''}{m.change_pct?.toFixed(2)}%
                  </span>
                  <span className="mv-px">{m.price != null ? `$${m.price.toFixed(2)}` : '—'}</span>
                  <span className="mv-rvol" title="Relativ volym">{m.rvol != null ? `${m.rvol.toFixed(1)}×` : '—'}</span>
                  <button
                    className="mv-add"
                    title={m.on_watchlist ? 'Redan i watchlist' : `Lägg till ${m.symbol}`}
                    disabled={m.on_watchlist || (add.isPending && add.variables === m.symbol)}
                    onClick={() => add.mutate(m.symbol)}
                  >
                    {m.on_watchlist ? '✓' : (add.isPending && add.variables === m.symbol ? <span className="spinner" /> : '＋')}
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
