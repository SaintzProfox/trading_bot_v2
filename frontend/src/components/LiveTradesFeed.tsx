'use client'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

interface Trade {
  id: number
  ticket: number
  direction: string
  lot_size: number
  entry_price: number
  stop_loss: number
  take_profit: number
  strategy: string
  opened_at: string
  pnl?: number
}

export default function LiveTradesFeed({ trades }: { trades: Trade[] }) {
  if (!trades || trades.length === 0) {
    return (
      <div className="text-center py-10 text-white/20 text-sm">
        No active positions
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-[10px] uppercase tracking-widest text-white/30">
            <th className="text-left pb-3">Ticket</th>
            <th className="text-left pb-3">Direction</th>
            <th className="text-right pb-3">Lots</th>
            <th className="text-right pb-3">Entry</th>
            <th className="text-right pb-3">SL</th>
            <th className="text-right pb-3">TP</th>
            <th className="text-right pb-3">Strategy</th>
            <th className="text-right pb-3">Opened</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.id} className="table-row">
              <td className="py-3 font-mono text-white/50">{trade.ticket || trade.id}</td>
              <td className="py-3">
                <div className={`flex items-center gap-1.5 font-semibold
                               ${trade.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {trade.direction === 'BUY'
                    ? <ArrowUpRight className="w-3.5 h-3.5" />
                    : <ArrowDownRight className="w-3.5 h-3.5" />
                  }
                  {trade.direction}
                </div>
              </td>
              <td className="py-3 text-right font-mono text-white/70">{trade.lot_size}</td>
              <td className="py-3 text-right font-mono text-white/70">{trade.entry_price?.toFixed(2)}</td>
              <td className="py-3 text-right font-mono text-red-400/70">{trade.stop_loss?.toFixed(2)}</td>
              <td className="py-3 text-right font-mono text-emerald-400/70">{trade.take_profit?.toFixed(2)}</td>
              <td className="py-3 text-right">
                <span className="badge badge-blue">{trade.strategy}</span>
              </td>
              <td className="py-3 text-right text-white/30 text-xs">
                {new Date(trade.opened_at).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
