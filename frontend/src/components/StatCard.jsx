import React from 'react'

export default function StatCard({ label, value, accent = false }) {
  return (
    <div className="bg-card rounded-xl border border-slate-200 p-5">
      <p className="text-xs uppercase tracking-wide text-slate-500 font-medium">{label}</p>
      <p className={`mt-2 text-3xl font-display font-semibold ${accent ? 'text-risk-high' : 'text-ink'}`}>
        {value}
      </p>
    </div>
  )
}
