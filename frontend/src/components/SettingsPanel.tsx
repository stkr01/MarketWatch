import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

interface Setting {
  key: string
  label: string
  help: string
  value: number
  default: number
  min: number
  max: number
  step: number
  unit: string
}

export default function SettingsPanel() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<{ settings: Setting[] }>({
    queryKey: ['settings'],
    queryFn: () => apiClient.get('/settings').then(r => r.data),
  })

  // Local slider positions while dragging (before the value is committed).
  const [local, setLocal] = useState<Record<string, number>>({})

  const mutate = useMutation({
    mutationFn: (v: { key: string; value: number }) =>
      apiClient.patch('/settings', v).then(r => r.data as { key: string; value: number }),
    onSuccess: resp => {
      // Reflect any server-side clamping, then refresh dependents.
      setLocal(p => ({ ...p, [resp.key]: resp.value }))
      qc.invalidateQueries({ queryKey: ['settings'] })
      qc.invalidateQueries({ queryKey: ['alerts'] })
    },
  })

  const commit = (key: string, value: number) => mutate.mutate({ key, value })
  const settings = data?.settings ?? []

  return (
    <div className="panel" style={{ marginBottom: '1.5rem' }}>
      <div className="panel-header">
        <div className="panel-title">⚙ Screener Settings</div>
      </div>

      <div className="settings-body">
        {isLoading ? (
          <div className="loading" style={{ padding: '1.25rem' }}><span className="spinner" />Loading…</div>
        ) : (
          settings.map(s => {
            const val = local[s.key] ?? s.value
            const pct = ((val - s.min) / (s.max - s.min)) * 100
            const changed = Math.abs(val - s.default) > 1e-9
            return (
              <div className="setting-row" key={s.key}>
                <div className="setting-head">
                  <span className="setting-label">{s.label}</span>
                  <span className="setting-val">{val.toFixed(1)}{s.unit}</span>
                </div>
                <input
                  type="range"
                  className="setting-slider"
                  min={s.min}
                  max={s.max}
                  step={s.step}
                  value={val}
                  style={{ ['--pct' as string]: `${pct}%` }}
                  onChange={e => setLocal(p => ({ ...p, [s.key]: parseFloat(e.target.value) }))}
                  onPointerUp={e => commit(s.key, parseFloat((e.target as HTMLInputElement).value))}
                  onKeyUp={e => commit(s.key, parseFloat((e.target as HTMLInputElement).value))}
                />
                <div className="setting-foot">
                  <span className="setting-help">{s.help}</span>
                  {changed && (
                    <button
                      className="setting-reset"
                      onClick={() => { setLocal(p => ({ ...p, [s.key]: s.default })); commit(s.key, s.default) }}
                    >
                      reset {s.default}{s.unit}
                    </button>
                  )}
                </div>
              </div>
            )
          })
        )}
        <div className="settings-note">Changes apply on the next scan · saved automatically</div>
      </div>
    </div>
  )
}
