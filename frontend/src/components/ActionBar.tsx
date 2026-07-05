import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import TraceButton from './TraceButton'

interface Props {
  onOpenNews: () => void
  onOpenHistory: () => void
}

/** Top action bar — home for global action buttons (scan, news analyser, …). */
export default function ActionBar({ onOpenNews, onOpenHistory }: Props) {
  const qc = useQueryClient()

  const { mutate: triggerScan, isPending } = useMutation({
    mutationKey: ['scan'],
    mutationFn: () => apiClient.post('/scan'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['candidates'] })
      qc.invalidateQueries({ queryKey: ['scan-status'] })
      setTimeout(() => {
        qc.refetchQueries({ queryKey: ['candidates'] })
        qc.refetchQueries({ queryKey: ['scan-status'] })
      }, 15000)
    },
  })

  return (
    <div className="action-bar">
      <TraceButton variant="green" onClick={() => triggerScan()} disabled={isPending}>
        {isPending ? <><span className="spinner" />Scanning…</> : <>◈ Scan Now</>}
      </TraceButton>
      <TraceButton variant="green" onClick={onOpenNews}>📰 News Analyser</TraceButton>
      <TraceButton variant="gold" onClick={onOpenHistory}>🕐 Historik</TraceButton>
    </div>
  )
}
