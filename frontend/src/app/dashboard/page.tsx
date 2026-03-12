'use client'
import { useEffect, useState, useCallback } from 'react'
import { TrendingUp, TrendingDown, Activity, DollarSign,
         Target, BarChart2, Zap, AlertTriangle } from 'lucide-react'
import BotControls from '@/components/BotControls'
import MetricCard from '@/components/MetricCard'
import EquityCurveChart from '@/components/EquityCurveChart'
import DailyPnlChart from '@/components/DailyPnlChart'
import LiveTradesFeed from '@/components/LiveTradesFeed'
import { api } from '@/lib/api'

interface Summary {
  total_trades: number
  total_pnl: number
  win_rate: number
  profit_factor: number
  max_drawdown: number
  winning_trades: number
  losing_trades: number
  avg_win: number
  avg_loss: number
  total_profit: number
  total_loss: number
}

interface BotStatus {
  is_running: boolean
  is_connected: boolean
  status: string
  account?: {
    balance: number
    equity: number
    profit: number
    currency: string
  }
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null)
  const [equityCurve, setEquityCurve] = useState([])
  const [dailyMetrics, setDailyMetrics] = useState([])
  const [activeTrades, setActiveTrades] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [summaryRes, statusRes, equityRes, dailyRes, tradesRes] = await Promise.allSettled([
        api.get('/api/metrics/summary'),
        api.get('/api/bot/status'),
        api.get('/api/metrics/equity-curve'),
        api.get('/api/metrics/daily?days=30'),
        api.get('/api/trades/open'),
      ])
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value.data)
      if (statusRes.status === 'fulfilled') setBotStatus(statusRes.value.data)
      if (equityRes.status === 'fulfilled') setEquityCurve(equityRes.value.data)
      if (dailyRes.status === 'fulfilled') setDailyMetrics(dailyRes.value.data)
      if (tradesRes.status === 'fulfilled') setActiveTrades(tradesRes.value.data.trades || [])
    } catch (err) {
      console.error('Fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // refresh every 30s
    return () => clearInterval(interval)
  }, [fetchData])

  const pnlColor = (val: number) => val >= 0 ? 'text-emerald-400' : 'text-red-400'

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-white">
            Trading Dashboard
          </h1>
          <p className="text-white/40 text-sm mt-0.5">
            XAUUSD · HFM Broker · {new Date().toLocaleDateString('en-MY', { dateStyle: 'long' })}
          </p>
        </div>
        <BotControls status={botStatus} onRefresh={fetchData} />
      </div>

      {/* Account Summary */}
      {botStatus?.account && (
        <div className="card border-gold-500/20 bg-gradient-to-r from-gold-900/20 to-transparent">
          <div className="flex items-center gap-8 flex-wrap">
            <div>
              <span className="metric-label">Balance</span>
              <div className="font-display text-2xl font-bold text-gold-400 mt-1">
                ${botStatus.account.balance?.toLocaleString('en', { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <span className="metric-label">Equity</span>
              <div className="font-display text-2xl font-bold text-white mt-1">
                ${botStatus.account.equity?.toLocaleString('en', { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div>
              <span className="metric-label">Floating P/L</span>
              <div className={`font-display text-2xl font-bold mt-1 ${pnlColor(botStatus.account.profit || 0)}`}>
                {botStatus.account.profit >= 0 ? '+' : ''}${botStatus.account.profit?.toFixed(2)}
              </div>
            </div>
            <div className="ml-auto">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold
                             ${botStatus.is_running
                               ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
                               : 'bg-white/5 text-white/40 border border-white/10'}`}>
                <span className={`w-2 h-2 rounded-full ${botStatus.is_running ? 'bg-emerald-400 animate-pulse' : 'bg-white/30'}`} />
                {botStatus.is_running ? 'BOT ACTIVE' : 'BOT STOPPED'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total P/L"
          value={summary ? `$${summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl?.toFixed(2)}` : '--'}
          icon={DollarSign}
          trend={summary?.total_pnl >= 0 ? 'up' : 'down'}
          sub={`${summary?.total_trades || 0} total trades`}
          loading={loading}
        />
        <MetricCard
          label="Win Rate"
          value={summary ? `${summary.win_rate?.toFixed(1)}%` : '--'}
          icon={Target}
          trend={summary?.win_rate >= 50 ? 'up' : 'down'}
          sub={`${summary?.winning_trades || 0}W / ${summary?.losing_trades || 0}L`}
          loading={loading}
        />
        <MetricCard
          label="Profit Factor"
          value={summary ? summary.profit_factor?.toFixed(2) : '--'}
          icon={BarChart2}
          trend={summary?.profit_factor >= 1 ? 'up' : 'down'}
          sub="Gross profit / loss ratio"
          loading={loading}
        />
        <MetricCard
          label="Max Drawdown"
          value={summary ? `$${summary.max_drawdown?.toFixed(2)}` : '--'}
          icon={AlertTriangle}
          trend="down"
          sub="Peak-to-trough decline"
          loading={loading}
        />
      </div>

      {/* Secondary metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Avg Win"
          value={summary ? `$${summary.avg_win?.toFixed(2)}` : '--'}
          icon={TrendingUp}
          trend="up"
          sub="Per winning trade"
          loading={loading}
          size="sm"
        />
        <MetricCard
          label="Avg Loss"
          value={summary ? `$${Math.abs(summary.avg_loss || 0)?.toFixed(2)}` : '--'}
          icon={TrendingDown}
          trend="down"
          sub="Per losing trade"
          loading={loading}
          size="sm"
        />
        <MetricCard
          label="Active Trades"
          value={activeTrades.length.toString()}
          icon={Activity}
          trend="neutral"
          sub="Currently open"
          loading={loading}
          size="sm"
        />
        <MetricCard
          label="Total Profit"
          value={summary ? `$${summary.total_profit?.toFixed(2)}` : '--'}
          icon={Zap}
          trend="up"
          sub="Gross winning trades"
          loading={loading}
          size="sm"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest mb-4">
            Equity Curve
          </h3>
          <EquityCurveChart data={equityCurve} />
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest mb-4">
            Daily P/L (30 Days)
          </h3>
          <DailyPnlChart data={dailyMetrics} />
        </div>
      </div>

      {/* Live Trades */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest">
            Active Positions
          </h3>
          <span className="badge badge-gold">{activeTrades.length} Open</span>
        </div>
        <LiveTradesFeed trades={activeTrades} />
      </div>
    </div>
  )
}
