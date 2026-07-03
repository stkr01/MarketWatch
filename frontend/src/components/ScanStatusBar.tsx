import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { useEffect, useState } from 'react'
import TraceButton from './TraceButton'
import StatusBox from './StatusBox'

export default function ScanStatusBar() {
  const queryClient = useQueryClient()
  const [countdown, setCountdown] = useState<string>('—')

  const { data: status } = useQuery({
    queryKey: ['scan-status'],
    queryFn: () => apiClient.get('/scan/status').then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: candidates = [] } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => apiClient.get('/candidates').then(r => r.data),
    refetchInterval: 30000,
  })

  const { mutate: triggerScan, isPending } = useMutation({
    mutationFn: () => apiClient.post('/scan'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      queryClient.invalidateQueries({ queryKey: ['scan-status'] })
      setTimeout(() => {
        queryClient.refetchQueries({ queryKey: ['candidates'] })
        queryClient.refetchQueries({ queryKey: ['scan-status'] })
      }, 15000)
    },
  })

  useEffect(() => {
    if (!status?.next_scan) {
      setCountdown('Pending…')
      return
    }
    const tick = () => {
      const diff = new Date(status.next_scan).getTime() - Date.now()
      if (diff > 0) {
        const m = Math.floor(diff / 60000)
        const s = Math.floor((diff % 60000) / 1000)
        setCountdown(`${m}m ${s.toString().padStart(2, '0')}s`)
      } else {
        setCountdown('Scanning soon…')
      }
    }
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [status?.next_scan])

  const lastScan = status?.last_scan
    ? new Date(status.last_scan).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : 'Never'

  return (
    <div className="stat-bar">
      <div className="stat-card">
        <div className="stat-label">Candidates</div>
        <div className="stat-value accent">{candidates.length}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Last Scan</div>
        <div className="stat-value">{lastScan}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Next Scan</div>
        <div className="stat-value">{countdown}</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Status</div>
        <div style={{ marginTop: '0.15rem' }}>
          <StatusBox
            chip
            tone={isPending ? 'orange' : 'green'}
            title={isPending ? 'Scanning' : 'Online'}
          />
        </div>
      </div>
      <div className="scan-action">
        <TraceButton variant="green" always onClick={() => triggerScan()} disabled={isPending}>
          {isPending ? <><span className="spinner" />Scanning…</> : <>◈ Scan Now</>}
        </TraceButton>
      </div>
    </div>
  )
}
