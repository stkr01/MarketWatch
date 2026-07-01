import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { yahooUrl } from '../utils'

interface WlItem { symbol: string; name?: string; exchange?: string }

export default function Watchlist() {
  const qc = useQueryClient()
  const [symbol, setSymbol] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { data: items = [], isLoading } = useQuery<WlItem[]>({
    queryKey: ['watchlist'],
    queryFn: () => apiClient.get('/watchlist').then(r => r.data),
  })

  const add = useMutation({
    mutationFn: (sym: string) => apiClient.post('/watchlist', { symbol: sym }),
    onSuccess: () => {
      setSymbol('')
      setError(null)
      qc.invalidateQueries({ queryKey: ['watchlist'] })
    },
    onError: (e: any) => setError(e?.response?.data?.detail || 'Could not add ticker'),
  })

  const remove = useMutation({
    mutationFn: (sym: string) => apiClient.delete(`/watchlist/${sym}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const sym = symbol.trim().toUpperCase()
    if (sym) add.mutate(sym)
  }

  return (
    <div className="panel" style={{ marginBottom: '1.5rem' }}>
      <div className="panel-header">
        <div className="panel-title">
          ⭐ Watchlist
          <span className="count">{items.length}</span>
        </div>
      </div>

      <div className="panel-pad">
        <form className="wl-form" onSubmit={submit}>
          <input
            className="wl-input"
            placeholder="Add ticker (e.g. PLTR)"
            value={symbol}
            maxLength={10}
            onChange={(e) => { setSymbol(e.target.value.toUpperCase()); setError(null) }}
          />
          <button type="submit" disabled={add.isPending || !symbol.trim()}>
            {add.isPending ? <span className="spinner" /> : '＋'}
          </button>
        </form>
        {error && <div className="wl-error">{error}</div>}

        {isLoading ? (
          <div className="loading" style={{ padding: '1rem' }}><span className="spinner" />Loading…</div>
        ) : items.length === 0 ? (
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginTop: '0.75rem' }}>
            Watchlist is empty — add a ticker to scan it.
          </p>
        ) : (
          <div className="wl-chips">
            {items.map((it) => (
              <span className="wl-chip" key={it.symbol}>
                <a href={yahooUrl(it.symbol)} target="_blank" rel="noopener noreferrer" title="Open on Yahoo Finance">
                  {it.symbol}
                </a>
                <button
                  title={`Remove ${it.symbol}`}
                  onClick={() => remove.mutate(it.symbol)}
                  disabled={remove.isPending}
                >✕</button>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
