'use client'
import { useEffect, useState } from 'react'
import { Save, RefreshCw, Info } from 'lucide-react'
import { api } from '@/lib/api'

const TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
const MA_TYPES = ['EMA', 'SMA']

interface Settings {
  timeframe: string
  rsi_period: number
  rsi_oversold: number
  rsi_overbought: number
  fast_ma_period: number
  slow_ma_period: number
  ma_type: string
  atr_period: number
  atr_multiplier_sl: number
  atr_multiplier_tp: number
  risk_per_trade_pct: number
  max_lot_size: number
  daily_loss_limit_pct: number
  max_open_trades: number
  min_signal_strength: number
  use_ml_filter: boolean
  check_interval_seconds: number
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.get('/api/settings/').then(r => {
      setSettings(r.data)
      setLoading(false)
    })
  }, [])

  const set = (key: keyof Settings, value: any) => {
    setSettings(prev => prev ? { ...prev, [key]: value } : prev)
  }

  const save = async () => {
    if (!settings) return
    setSaving(true)
    try {
      await api.put('/api/settings/', settings)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-40 text-white/30">Loading settings...</div>
  }
  if (!settings) return null

  return (
    <div className="space-y-6 max-w-3xl animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-white">Strategy Settings</h1>
          <p className="text-white/40 text-sm mt-0.5">Configure trading parameters and risk management</p>
        </div>
        <button
          onClick={save}
          disabled={saving}
          className={`btn-primary flex items-center gap-2 ${saved ? '!bg-emerald-500' : ''}`}
        >
          {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Timeframe & MA */}
      <Section title="Strategy Parameters">
        <Row label="Timeframe" hint="Chart timeframe for signal generation">
          <select className="input w-40" value={settings.timeframe}
                  onChange={e => set('timeframe', e.target.value)}>
            {TIMEFRAMES.map(tf => <option key={tf} value={tf}>{tf}</option>)}
          </select>
        </Row>
        <Row label="MA Type">
          <select className="input w-40" value={settings.ma_type}
                  onChange={e => set('ma_type', e.target.value)}>
            {MA_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </Row>
        <Row label="Fast MA Period" hint="Short-term moving average period">
          <NumberInput value={settings.fast_ma_period} min={5} max={100}
                       onChange={v => set('fast_ma_period', v)} />
        </Row>
        <Row label="Slow MA Period" hint="Long-term moving average period">
          <NumberInput value={settings.slow_ma_period} min={20} max={200}
                       onChange={v => set('slow_ma_period', v)} />
        </Row>
        <Row label="RSI Period">
          <NumberInput value={settings.rsi_period} min={5} max={50}
                       onChange={v => set('rsi_period', v)} />
        </Row>
        <Row label="RSI Oversold Level">
          <NumberInput value={settings.rsi_oversold} min={10} max={45}
                       onChange={v => set('rsi_oversold', v)} />
        </Row>
        <Row label="RSI Overbought Level">
          <NumberInput value={settings.rsi_overbought} min={55} max={90}
                       onChange={v => set('rsi_overbought', v)} />
        </Row>
        <Row label="ATR Period">
          <NumberInput value={settings.atr_period} min={5} max={30}
                       onChange={v => set('atr_period', v)} />
        </Row>
        <Row label="ATR SL Multiplier" hint="Stop loss = price ± ATR × multiplier">
          <NumberInput value={settings.atr_multiplier_sl} min={0.5} max={5} step={0.1}
                       onChange={v => set('atr_multiplier_sl', v)} />
        </Row>
        <Row label="ATR TP Multiplier" hint="Take profit = price ± ATR × multiplier">
          <NumberInput value={settings.atr_multiplier_tp} min={0.5} max={10} step={0.1}
                       onChange={v => set('atr_multiplier_tp', v)} />
        </Row>
      </Section>

      {/* Risk Management */}
      <Section title="Risk Management">
        <Row label="Risk Per Trade (%)" hint="% of account balance risked per trade">
          <NumberInput value={settings.risk_per_trade_pct} min={0.1} max={5} step={0.1}
                       onChange={v => set('risk_per_trade_pct', v)} />
        </Row>
        <Row label="Max Lot Size">
          <NumberInput value={settings.max_lot_size} min={0.01} max={100} step={0.01}
                       onChange={v => set('max_lot_size', v)} />
        </Row>
        <Row label="Daily Loss Limit (%)" hint="Bot stops after hitting this daily loss %">
          <NumberInput value={settings.daily_loss_limit_pct} min={0} max={20} step={0.5}
                       onChange={v => set('daily_loss_limit_pct', v)} />
        </Row>
        <Row label="Max Open Trades">
          <NumberInput value={settings.max_open_trades} min={1} max={10}
                       onChange={v => set('max_open_trades', v)} />
        </Row>
        <Row label="Min Signal Strength" hint="Only trade signals above this score (0-100)">
          <NumberInput value={settings.min_signal_strength} min={0} max={100}
                       onChange={v => set('min_signal_strength', v)} />
        </Row>
      </Section>

      {/* ML & Automation */}
      <Section title="AI & Automation">
        <Row label="Use ML Filter" hint="Apply machine learning signal classifier">
          <button
            onClick={() => set('use_ml_filter', !settings.use_ml_filter)}
            className={`w-12 h-6 rounded-full transition-all relative
                       ${settings.use_ml_filter ? 'bg-gold-500' : 'bg-white/10'}`}
          >
            <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all shadow
                             ${settings.use_ml_filter ? 'left-6' : 'left-0.5'}`} />
          </button>
        </Row>
        <Row label="Check Interval (seconds)" hint="How often the bot scans for signals">
          <NumberInput value={settings.check_interval_seconds} min={10} max={3600}
                       onChange={v => set('check_interval_seconds', v)} />
        </Row>
      </Section>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card space-y-0 divide-y divide-white/5">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-gold-400 pb-4">{title}</h2>
      {children}
    </div>
  )
}

function Row({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-4">
      <div>
        <div className="text-sm text-white/80 font-medium">{label}</div>
        {hint && <div className="text-xs text-white/30 mt-0.5">{hint}</div>}
      </div>
      {children}
    </div>
  )
}

function NumberInput({ value, min, max, step = 1, onChange }: {
  value: number; min: number; max: number; step?: number; onChange: (v: number) => void
}) {
  return (
    <input
      type="number"
      className="input w-32 text-right font-mono"
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={e => onChange(parseFloat(e.target.value) || min)}
    />
  )
}
