import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'

export default function ScanStatusBar() {
  const queryClient = useQueryClient()

  const { data: status } = useQuery({
    queryKey: ['scan-status'],
    queryFn: () => apiClient.get('/scan/status').then(r => r.data),
    refetchInterval: 10000, // Poll every 10 seconds
  })

  const { mutate: triggerScan, isPending } = useMutation({
    mutationFn: () => apiClient.post('/scan'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan-status'] })
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
    }
  })

  const formatTime = (date?: string) => {
    if (!date) return 'Never'
    return new Date(date).toLocaleTimeString()
  }

  return (
    <div className="scan-status-bar">
      <div className="status-info">
        <p>Last Scan: {formatTime(status?.last_scan)}</p>
        <p>Next Scan: {formatTime(status?.next_scan)}</p>
        {status?.is_running && <p className="running">⟳ Scanning in progress...</p>}
      </div>

      <button
        onClick={() => triggerScan()}
        disabled={isPending}
      >
        {isPending ? 'Scanning...' : 'Scan Now'}
      </button>
    </div>
  )
}
