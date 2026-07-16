import React from 'react'

const STYLES = {
  HIGH: 'bg-risk-high/10 text-risk-high border-risk-high/30',
  MODERATE: 'bg-risk-moderate/10 text-risk-moderate border-risk-moderate/30',
  LOW: 'bg-risk-low/10 text-risk-low border-risk-low/30',
}

export default function RiskBadge({ level, size = 'md' }) {
  const cls = STYLES[level] || 'bg-slate-100 text-slate-600 border-slate-300'
  const sizeCls = size === 'lg' ? 'text-sm px-3 py-1.5' : 'text-xs px-2.5 py-1'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-medium ${cls} ${sizeCls}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {level} RISK
    </span>
  )
}
