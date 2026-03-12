'use client'
import { useEffect, useState } from 'react'
import { ArrowUpRight, ArrowDownRight, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '@/lib/api'

export default function TradesPage() {
  const [trades, setTrades] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const LIMIT = 20

  useEffect(() => {
    setLoading(true)
    api.get(`/api/trades/?page=${page}&limit=${LIMIT}`)
      .then(r => {
        setTrades(r.data.trades)
        setTotal(r.data.total)
      })
      .finally(() => setLoading(false))
  }, [page])

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div className="space-y-6 animate-fade-up">
      <div>
        <h1 className="font-display text-2xl font-bold text-white">Trade History</h1>
        <p className="text-white/40 text-sm mt-0.5">{total} total trades recorded</p>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase tracking-widest text-white/30">
                <th className="text-left pb-4">ID</th>
                <th className="text-left pb-4">Direction</th>
                <th className="text-right pb-4">Lots</th>
                <th className="text-right pb-4">Entry</th>
                <th className="text-right pb-4">Exit</th>
                <th className="text-right pb-4">SL</th>
                <th className="text-right pb-4">TP</th>
                <th className="text-right pb-4">P/L</th>
                <th className="text-right pb-4">Strategy</th>
                <th className="text-right pb-4">Status</th>
                <th className="text-right pb-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} className="border-b border-white/5">
                    {Array.from({ length: 11 }).map((_, j) => (
                      <td key={j} className="py-3">
                        <div className="h-4 bg-white/5 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : trades.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-white/20">
                    No trades yet
                  </td>
                </tr>
              ) : (
                trades.map((t: any) => (
                  <tr key={t.id} className="table-row">
                    <td className="py-3 font-mono text-white/40 text-xs">{t.ticket || t.id}</td>
                    <td className="py-3">
                      <div className={`flex items-center gap-1 font-semibold
                                     ${t.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                        {t.direction === 'BUY'
                          ? <ArrowUpRight className="w-3 h-3" />
                          : <ArrowDownRight className="w-3 h-3" />
                        }
                        {t.direction}
                      </div>
                    </td>
                    <td className="py-3 text-right font-mono text-white/60">{t.lot_size}</td>
                    <td className="py-3 text-right font-mono text-white/60">{t.entry_price?.toFixed(2)}</td>
                    <td className="py-3 text-right font-mono text-white/60">
                      {t.exit_price?.toFixed(2) || '--'}
                    </td>
                    <td className="py-3 text-right font-mono text-red-400/60">{t.stop_loss?.toFixed(2)}</td>
                    <td className="py-3 text-right font-mono text-emerald-400/60">{t.take_profit?.toFixed(2)}</td>
                    <td className={`py-3 text-right font-mono font-semibold
                                   ${(t.pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {t.pnl != null
                        ? `${t.pnl >= 0 ? '+' : ''}$${t.pnl.toFixed(2)}`
                        : '--'}
                    </td>
                    <td className="py-3 text-right">
                      <span className="badge badge-blue">{t.strategy}</span>
                    </td>
                    <td className="py-3 text-right">
                      <span className={t.status === 'open' ? 'badge badge-gold' : 'badge badge-green'}>
                        {t.status}
                      </span>
                    </td>
                    <td className="py-3 text-right text-white/30 text-xs whitespace-nowrap">
                      {new Date(t.opened_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/5">
            <span className="text-xs text-white/30">
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-ghost p-2 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-ghost p-2 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
