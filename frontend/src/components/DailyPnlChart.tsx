'use client'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell
} from 'recharts'

const TOOLTIP_STYLE = {
  backgroundColor: '#1a1a35',
  border: '1px solid rgba(245,158,11,0.25)',
  borderRadius: '8px',
  color: '#fff',
  fontSize: '12px',
}

export default function DailyPnlChart({ data }: { data: any[] }) {
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
        <Bar dataKey="daily_pnl" radius={[3, 3, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.daily_pnl >= 0 ? '#10b981' : '#ef4444'}
              fillOpacity={0.8}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
