// MetricCard.tsx
'use client'
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface Props {
  label: string
  value: string
  icon: LucideIcon
  trend: 'up' | 'down' | 'neutral'
  sub?: string
  loading?: boolean
  size?: 'default' | 'sm'
}

export default function MetricCard({ label, value, icon: Icon, trend, sub, loading, size = 'default' }: Props) {
  const trendColor = trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-white/40'
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus

  return (
    <div className="card-hover">
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center"
             style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.12)' }}>
          <Icon className="w-4 h-4 text-gold-400" />
        </div>
        <TrendIcon className={`w-4 h-4 ${trendColor}`} />
      </div>

      {loading ? (
        <div className="space-y-2">
          <div className="h-7 bg-white/5 rounded animate-pulse w-3/4" />
          <div className="h-3 bg-white/5 rounded animate-pulse w-1/2" />
        </div>
      ) : (
        <>
          <div className={`font-display font-bold ${trendColor} ${size === 'sm' ? 'text-xl' : 'text-2xl'}`}>
            {value}
          </div>
          <div className="text-[10px] uppercase tracking-widest text-white/30 mt-1 font-medium">
            {label}
          </div>
          {sub && <div className="text-xs text-white/25 mt-0.5">{sub}</div>}
        </>
      )}
    </div>
  )
}
