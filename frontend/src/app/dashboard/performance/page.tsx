'use client'
import { useEffect, useState } from 'react'
import { EquityCurveChart } from '@/components/EquityCurveChart'
import DailyPnlChart from '@/components/DailyPnlChart'
import { api } from '@/lib/api'

export default function PerformancePage() {
  const [summary, setSummary] = useState<any>(null)
  const [equity, setEquity] = useState([])
  const [daily, setDaily] = useState([])
  const [drawdown, setDrawdown] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/metrics/summary'),
      api.get('/api/metrics/equity-curve'),
      api.get('/api/metrics/daily?days=60'),
      api.get('/api/metrics/drawdown'),
    ]).then(([s, e, d, dd]) => {
      setSummary(s.data)
      setEquity(e.data)
      setDaily(d.data)
      setDrawdown(dd.data)
    }).finally(() => setLoading(false))
  }, [])

  const fmt = (v: number, prefix = '$') => v >= 0 ? `${prefix}+${v?.toFixed(2)}` : `${prefix}${v?.toFixed(2)}`

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-bold text-white">Performance Analytics</h1>
        <p className="text-white/40 text-sm mt-0.5">Comprehensive strategy performance analysis</p>
      </div>

      {/* Summary stats grid */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total P/L', value: `$${summary.total_pnl?.toFixed(2)}`, pos: summary.total_pnl >= 0 },
            { label: 'Win Rate', value: `${summary.win_rate?.toFixed(1)}%`, pos: summary.win_rate >= 50 },
            { label: 'Profit Factor', value: summary.profit_factor?.toFixed(3), pos: summary.profit_factor >= 1 },
            { label: 'Max Drawdown', value: `$${summary.max_drawdown?.toFixed(2)}`, pos: false },
            { label: 'Total Trades', value: summary.total_trades?.toString(), pos: true },
            { label: 'Winning Trades', value: summary.winning_trades?.toString(), pos: true },
            { label: 'Avg Win', value: `$${summary.avg_win?.toFixed(2)}`, pos: true },
            { label: 'Avg Loss', value: `$${Math.abs(summary.avg_loss || 0)?.toFixed(2)}`, pos: false },
          ].map((item) => (
            <div key={item.label} className="card-hover text-center">
              <div className={`font-display text-2xl font-bold ${item.pos ? 'text-emerald-400' : 'text-red-400'}`}>
                {item.value}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-white/30 mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest mb-4">
          Equity Curve (All Time)
        </h3>
        <EquityCurveChart data={equity} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest mb-4">
            Daily P/L (60 Days)
          </h3>
          <DailyPnlChart data={daily} />
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest mb-4">
            Drawdown Analysis
          </h3>
          {drawdown?.data?.length > 0 ? (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-white/40">Max Drawdown</span>
                <span className="text-red-400 font-mono">${Math.abs(drawdown.max_drawdown)?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white/40">Max Drawdown %</span>
                <span className="text-red-400 font-mono">{Math.abs(drawdown.max_drawdown_pct)?.toFixed(2)}%</span>
              </div>
              <div className="mt-4">
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full transition-all"
                    style={{ width: `${Math.min(Math.abs(drawdown.max_drawdown_pct), 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-white/20 mt-1">
                  <span>0%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-white/20 text-sm text-center py-8">No drawdown data</div>
          )}
        </div>
      </div>
    </div>
  )
}
