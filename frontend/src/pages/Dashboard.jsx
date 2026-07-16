import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client.js'
import AppShell from '../components/AppShell.jsx'
import StatCard from '../components/StatCard.jsx'
import { formatLocalDate } from '../utils/time.js'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [patients, setPatients] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/dashboard/stats').then((r) => setStats(r.data)).catch(() => setError('Could not load stats.'))
    client.get('/patients').then((r) => setPatients(r.data.slice(0, 8))).catch(() => {})
  }, [])

  return (
    <AppShell>
      <div className="p-8 max-w-6xl">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink">Dashboard</h1>
            <p className="text-sm text-slate-500 mt-0.5">Today at a glance</p>
          </div>
          <Link to="/patients" className="bg-ink text-white text-sm rounded-lg px-4 py-2.5 hover:bg-ink/90">
            + New Patient
          </Link>
        </header>

        {error && <p className="text-risk-high text-sm mb-4">{error}</p>}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <StatCard label="Today's Patients" value={stats?.todays_patients ?? '–'} />
          <StatCard label="Predictions Today" value={stats?.predictions_today ?? '–'} />
          <StatCard label="High Risk Cases" value={stats?.high_risk_cases ?? '–'} accent />
          <StatCard label="Normal ECG" value={stats?.normal_ecg ?? '–'} />
        </div>

        <div className="bg-card rounded-xl border border-slate-200">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-display font-semibold text-ink text-sm">Recent Patients</h2>
            <Link to="/patients" className="text-xs text-tealline hover:underline">View all →</Link>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wide">
                <th className="px-5 py-2 font-medium">Patient ID</th>
                <th className="px-5 py-2 font-medium">Name</th>
                <th className="px-5 py-2 font-medium">Registered</th>
                <th className="px-5 py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {patients.length === 0 && (
                <tr><td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                  No patients yet — register your first patient to get started.
                </td></tr>
              )}
              {patients.map((p) => (
                <tr key={p.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-5 py-3 font-mono text-xs">{p.patient_code}</td>
                  <td className="px-5 py-3">{p.name}</td>
                  <td className="px-5 py-3 text-slate-500">{formatLocalDate(p.created_at)}</td>
                  <td className="px-5 py-3 text-right">
                    <Link to={`/patients/${p.patient_code}`} className="text-tealline text-xs hover:underline">
                      Open →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  )
}
