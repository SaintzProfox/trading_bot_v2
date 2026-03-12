'use client'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  BarChart, Bar, ResponsiveContainer, ReferenceLine
} from 'recharts'

const TOOLTIP_STYLE = {
  backgroundColor: '#1a1a35',
  border: '1px solid rgba(245,158,11,0.25)',
  borderRadius: '8px',
  color: '#fff',
  fontSize: '12px',
}

export function EquityCurveChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-white/20 text-sm">
        No equity data yet
      </div>
    )
  }

  const minEquity = Math.min(...data.map(d => d.equity))
  const maxEquity = Math.max(...data.map(d => d.equity))
  const domain = [minEquity * 0.995, maxEquity * 1.005]

  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }}
          tickLine={false}
          axisLine={false}
          domain={domain}
          tickFormatter={v => `$${v.toLocaleString()}`}
          width={70}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: any) => [`$${Number(v).toLocaleString('en', { minimumFractionDigits: 2 })}`, 'Equity']}
        />
        <Area
          type="monotone"
          dataKey="equity"
          stroke="#f59e0b"
          strokeWidth={2}
          fill="url(#equityGrad)"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function DailyPnlChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-white/20 text-sm">
        No daily data yet
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 5, right: 5, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
        <XAxis
          dataKey="day"
          tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `$${v}`}
          width={55}
        />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(v: any) => [`$${Number(v).toFixed(2)}`, 'Daily P/L']}
        />
        <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
        <Bar
          dataKey="daily_pnl"
          radius={[3, 3, 0, 0]}
          fill="#10b981"
          // Color bars: green for profit, red for loss
          label={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default EquityCurveChart
