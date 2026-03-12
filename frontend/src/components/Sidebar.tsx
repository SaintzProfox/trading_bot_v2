'use client'
import { usePathname, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useState } from 'react'
import {
  LayoutDashboard, TrendingUp, History, Settings,
  ChevronLeft, ChevronRight, LogOut, Bot
} from 'lucide-react'
import Cookies from 'js-cookie'

const NAV = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/dashboard/trades', icon: History, label: 'Trade History' },
  { href: '/dashboard/performance', icon: TrendingUp, label: 'Performance' },
  { href: '/dashboard/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()
  const router = useRouter()

  const logout = () => {
    Cookies.remove('token')
    localStorage.removeItem('user')
    router.push('/')
  }

  return (
    <aside className={`relative flex flex-col h-screen border-r border-gold-500/10
                       bg-surface-900 transition-all duration-300
                       ${collapsed ? 'w-16' : 'w-56'}`}>
      {/* Logo */}
      <div className={`flex items-center gap-3 px-4 py-5 border-b border-gold-500/10
                       ${collapsed ? 'justify-center' : ''}`}>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
             style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.25), rgba(245,158,11,0.05))',
                      border: '1px solid rgba(245,158,11,0.25)' }}>
          <Bot className="w-5 h-5 text-gold-400" />
        </div>
        {!collapsed && (
          <div>
            <div className="font-display font-bold text-sm gold-text">AuraTrade</div>
            <div className="text-[10px] text-white/30 uppercase tracking-wider">XAUUSD Bot</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm
                         transition-all duration-150 group
                         ${collapsed ? 'justify-center' : ''}
                         ${active
                           ? 'bg-gold-500/15 text-gold-400 border border-gold-500/20'
                           : 'text-white/40 hover:text-white/80 hover:bg-white/5'}`}
              title={collapsed ? label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-gold-400' : ''}`} />
              {!collapsed && <span className="font-medium">{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="px-2 pb-4 space-y-1">
        <button
          onClick={logout}
          className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm
                     text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all
                     ${collapsed ? 'justify-center' : ''}`}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full
                   bg-surface-900 border border-gold-500/20 flex items-center justify-center
                   text-white/40 hover:text-gold-400 transition-colors z-10"
      >
        {collapsed
          ? <ChevronRight className="w-3 h-3" />
          : <ChevronLeft className="w-3 h-3" />
        }
      </button>
    </aside>
  )
}
