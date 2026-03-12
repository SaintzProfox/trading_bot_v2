'use client'
import { useState } from 'react'
import { Play, Square, AlertOctagon, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

interface Props {
  status: any
  onRefresh: () => void
}

export default function BotControls({ status, onRefresh }: Props) {
  const [loading, setLoading] = useState<string | null>(null)

  const action = async (endpoint: string, label: string) => {
    setLoading(label)
    try {
      await api.post(`/api/bot/${endpoint}`)
      setTimeout(onRefresh, 500)
    } catch (err: any) {
      alert(err.response?.data?.detail || `${label} failed`)
    } finally {
      setLoading(null)
    }
  }

  const isRunning = status?.is_running

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onRefresh}
        className="btn-ghost p-2.5"
        title="Refresh"
      >
        <RefreshCw className="w-4 h-4" />
      </button>

      {!isRunning ? (
        <button
          onClick={() => action('start', 'start')}
          disabled={loading === 'start'}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          {loading === 'start' ? 'Starting...' : 'Start Bot'}
        </button>
      ) : (
        <button
          onClick={() => action('stop', 'stop')}
          disabled={loading === 'stop'}
          className="btn-ghost flex items-center gap-2 disabled:opacity-50"
        >
          <Square className="w-4 h-4" />
          {loading === 'stop' ? 'Stopping...' : 'Stop Bot'}
        </button>
      )}

      <button
        onClick={() => {
          if (confirm('Close ALL open positions and stop bot?')) {
            action('emergency-stop', 'emergency')
          }
        }}
        disabled={loading === 'emergency'}
        className="btn-danger flex items-center gap-2 disabled:opacity-50"
        title="Emergency Stop"
      >
        <AlertOctagon className="w-4 h-4" />
        {loading === 'emergency' ? 'Stopping...' : 'E-Stop'}
      </button>
    </div>
  )
}
