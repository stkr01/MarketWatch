import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { useEffect, useState } from 'react'

export default function ScanStatusBar() {
  const queryClient = useQueryClient()
  const [nextScanCountdown, setNextScanCountdown] = useState<string>('')

  const { data: status, isLoading } = useQuery({
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

  // Update countdown timer
  useEffect(() => {
    if (!status?.next_scan) return

    const updateCountdown = () => {
      const now = new Date()
      const nextScan = new Date(status.next_scan)
      const diff = nextScan.getTime() - now.getTime()

      if (diff > 0) {
        const minutes = Math.floor(diff / 60000)
        const seconds = Math.floor((diff % 60000) / 1000)
        setNextScanCountdown(`${minutes}m ${seconds}s`)
      } else {
        setNextScanCountdown('Scanning soon...')
      }
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [status?.next_scan])

  const formatDateTime = (date?: string) => {
    if (!date) return 'Never'
    const d = new Date(date)
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
  }

  return (
    <div className="scan-status-bar">
      <div className="status-info">
        <div>
          <strong>Last Scan:</strong>
          <span style={{ marginLeft: '0.5rem', color: '#e2e8f0' }}>
            {status?.last_scan ? new Date(status.last_scan).toLocaleTimeString() : 'Never'}
          </span>
        </div>

        <div>
          <strong>Next Scan:</strong>
          <span style={{ marginLeft: '0.5rem', color: '#60a5fa' }}>
            {nextScanCountdown || 'Computing...'}
          </span>
        </div>

        {status?.is_running && (
          <div style={{ color: '#16a34a', fontWeight: 500 }}>
            ⟳ Scanning in progress...
          </div>
        )}
      </div>

      <button
        onClick={() => triggerScan()}
        disabled={isPending}
        style={{
          padding: '0.75rem 1.5rem',
          background: isPending ? '#64748b' : '#10b981',
          whiteSpace: 'nowrap'
        }}
      >
        {isPending ? (
          <>⟳ Scanning...</>
        ) : (
          <>🔄 Scan Now</>
        )}
      </button>
    </div>
  )
}
