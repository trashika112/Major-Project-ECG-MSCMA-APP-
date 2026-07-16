import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: DashboardIcon },
  { to: '/patients', label: 'Patients', icon: PatientsIcon },
]

const ADMIN_NAV_ITEM = { to: '/admin', label: 'Admin', icon: AdminIcon }

export default function AppShell({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const navItems = user?.role === 'admin' ? [...NAV_ITEMS, ADMIN_NAV_ITEM] : NAV_ITEMS

  return (
    <div className="min-h-screen flex bg-canvas">
      <aside className="w-60 shrink-0 bg-ink text-white flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-2">
            <PulseMark />
            <span className="font-display font-semibold tracking-tight text-lg leading-tight">
              ECG&nbsp;CDSS
            </span>
          </div>
          <p className="text-[11px] text-white/50 mt-1 font-mono">MSCMA-Net v1</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive ? 'bg-white/10 text-white' : 'text-white/70 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <Icon />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/10">
          <p className="text-sm font-medium">{user?.full_name}</p>
          <p className="text-[11px] text-white/50 capitalize font-mono">{user?.role}</p>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="mt-3 text-xs text-white/70 hover:text-white underline underline-offset-2"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  )
}

function PulseMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      <path d="M1 11h4l2-7 4 14 3-11 2 4h5" stroke="#12877F" strokeWidth="1.8"
            strokeLinecap="round" strokeLinejoin="round" className="pulse-dot" />
    </svg>
  )
}

function DashboardIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="1" width="6" height="9" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="9" y="12" width="6" height="3" rx="1" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  )
}

function PatientsIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="6" cy="5" r="2.3" stroke="currentColor" strokeWidth="1.3" />
      <path d="M1.5 14c.5-3 2.2-4.5 4.5-4.5s4 1.5 4.5 4.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="12" cy="4.5" r="1.7" stroke="currentColor" strokeWidth="1.2" />
      <path d="M10.3 9.6c1.6-.3 3.2.6 3.7 2.9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  )
}

function AdminIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 1.5l5.5 2v3.8c0 3.4-2.3 6-5.5 7.2-3.2-1.2-5.5-3.8-5.5-7.2V3.5L8 1.5z"
            stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <path d="M5.7 8.1l1.6 1.6 3-3.2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
