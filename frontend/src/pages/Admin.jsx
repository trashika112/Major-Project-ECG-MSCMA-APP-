import React, { useEffect, useState } from 'react'
import Plotly from 'plotly.js-basic-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'
import client from '../api/client.js'
import AppShell from '../components/AppShell.jsx'
import { formatLocalDateTime } from '../utils/time.js'
import RiskBadge from '../components/RiskBadge.jsx'
import { useAuth } from '../context/AuthContext.jsx'

const Plot = createPlotlyComponent(Plotly)

const TABS = [
  { key: 'users', label: 'Users' },
  { key: 'logs', label: 'Prediction Logs' },
  { key: 'stats', label: 'Usage Statistics' },
]

export default function Admin() {
  const [tab, setTab] = useState('users')

  return (
    <AppShell>
      <div className="p-8 max-w-6xl">
        <header className="mb-6">
          <h1 className="font-display text-2xl font-semibold text-ink">Admin Panel</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage users, review prediction activity, and monitor usage</p>
        </header>

        <div className="flex gap-1 mb-6 border-b border-slate-200">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
                tab === t.key
                  ? 'border-tealline text-ink'
                  : 'border-transparent text-slate-500 hover:text-ink'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'users' && <UsersTab />}
        {tab === 'logs' && <LogsTab />}
        {tab === 'stats' && <StatsTab />}
      </div>
      <style>{`.input { border:1px solid #CBD5E1; border-radius:0.5rem; padding:0.5rem 0.7rem; font-size:0.85rem; background:white; }
                .input:focus { border-color:#12877F; outline:none; }`}</style>
    </AppShell>
  )
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------
const EMPTY_USER = { username: '', password: '', full_name: '', role: 'doctor' }

function UsersTab() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_USER)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function load() {
    client.get('/admin/users').then((r) => setUsers(r.data)).catch(() => setError('Could not load users.'))
  }
  useEffect(() => { load() }, [])

  async function onCreate(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      await client.post('/auth/users', form)
      setForm(EMPTY_USER)
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create this user.')
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(u) {
    if (!window.confirm(`Delete user "${u.username}"? This can't be undone.`)) return
    setError('')
    try {
      await client.delete(`/admin/users/${u.id}`)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not delete this user.')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-slate-500">{users.length} account{users.length === 1 ? '' : 's'}</p>
        <button onClick={() => setShowForm((s) => !s)}
                className="bg-ink text-white text-sm rounded-lg px-4 py-2.5 hover:bg-ink/90">
          {showForm ? 'Cancel' : '+ New User'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={onCreate} className="bg-card border border-slate-200 rounded-xl p-6 mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Field label="Username *">
            <input required value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} className="input" />
          </Field>
          <Field label="Password *">
            <input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input" />
          </Field>
          <Field label="Full Name">
            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="input" />
          </Field>
          <Field label="Role">
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="input">
              <option value="doctor">Doctor</option>
              <option value="cardiologist">Cardiologist</option>
              <option value="nurse">Nurse</option>
              <option value="admin">Admin</option>
            </select>
          </Field>
          {error && <p className="col-span-full text-sm text-risk-high">{error}</p>}
          <div className="col-span-full">
            <button disabled={saving} className="bg-tealline text-white text-sm rounded-lg px-5 py-2.5 hover:bg-tealline/90 disabled:opacity-60">
              {saving ? 'Creating…' : 'Create User'}
            </button>
          </div>
        </form>
      )}

      {!showForm && error && <p className="text-sm text-risk-high mb-4">{error}</p>}

      <div className="bg-card rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 uppercase tracking-wide">
              <th className="px-5 py-2 font-medium">Username</th>
              <th className="px-5 py-2 font-medium">Full Name</th>
              <th className="px-5 py-2 font-medium">Role</th>
              <th className="px-5 py-2 font-medium">Status</th>
              <th className="px-5 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">No users found.</td></tr>
            )}
            {users.map((u) => (
              <tr key={u.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-5 py-3 font-mono text-xs">{u.username}</td>
                <td className="px-5 py-3">{u.full_name || '–'}</td>
                <td className="px-5 py-3 text-slate-500 capitalize">{u.role}</td>
                <td className="px-5 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-risk-low/10 text-risk-low' : 'bg-slate-100 text-slate-500'}`}>
                    {u.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td className="px-5 py-3 text-right">
                  {u.username !== me?.username && (
                    <button onClick={() => onDelete(u)} className="text-risk-high text-xs hover:underline">
                      Delete
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Prediction logs
// ---------------------------------------------------------------------------
function LogsTab() {
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/admin/prediction-logs').then((r) => setLogs(r.data)).catch(() => setError('Could not load prediction logs.'))
  }, [])

  return (
    <div>
      {error && <p className="text-sm text-risk-high mb-4">{error}</p>}
      <div className="bg-card rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 uppercase tracking-wide">
              <th className="px-5 py-2 font-medium">Date</th>
              <th className="px-5 py-2 font-medium">Patient</th>
              <th className="px-5 py-2 font-medium">Doctor</th>
              <th className="px-5 py-2 font-medium">Format</th>
              <th className="px-5 py-2 font-medium">Prediction</th>
              <th className="px-5 py-2 font-medium">Confidence</th>
              <th className="px-5 py-2 font-medium">Risk</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && (
              <tr><td colSpan={7} className="px-5 py-8 text-center text-slate-400">No predictions yet.</td></tr>
            )}
            {logs.map((l) => (
              <tr key={l.prediction_id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-5 py-3 text-slate-500 font-mono text-xs">{formatLocalDateTime(l.created_at)}</td>
                <td className="px-5 py-3">
                  <span className="font-mono text-xs text-tealline">{l.patient_code}</span>
                  <span className="text-slate-500"> · {l.patient_name}</span>
                </td>
                <td className="px-5 py-3 text-slate-500">{l.doctor_name || '–'}</td>
                <td className="px-5 py-3 text-slate-500 uppercase text-xs font-mono">{l.file_format}</td>
                <td className="px-5 py-3 font-medium text-ink">{l.top_class}</td>
                <td className="px-5 py-3 font-mono text-xs text-slate-500">{(l.top_confidence * 100).toFixed(1)}%</td>
                <td className="px-5 py-3"><RiskBadge level={l.risk_level} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Usage statistics
// ---------------------------------------------------------------------------
function StatsTab() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/admin/usage-stats').then((r) => setStats(r.data)).catch(() => setError('Could not load usage statistics.'))
  }, [])

  if (error) return <p className="text-sm text-risk-high">{error}</p>
  if (!stats) return <p className="text-sm text-slate-400">Loading…</p>

  const barLayout = (title) => ({
    height: 260,
    margin: { l: 40, r: 10, t: 30, b: 40 },
    title: { text: title, font: { size: 12, family: 'Inter, sans-serif' } },
    font: { family: 'Inter, sans-serif', size: 10, color: '#334155' },
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    xaxis: { showgrid: false },
    yaxis: { showgrid: true, gridcolor: '#EEF2F6' },
  })

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <MiniStat label="Users" value={stats.total_users} />
        <MiniStat label="Patients" value={stats.total_patients} />
        <MiniStat label="ECG Records" value={stats.total_ecg_records} />
        <MiniStat label="Predictions" value={stats.total_predictions} />
        <MiniStat label="Avg. Confidence" value={`${(stats.avg_confidence * 100).toFixed(1)}%`} />
      </div>

      <div className="bg-card border border-slate-200 rounded-xl p-4 mb-6">
        <Plot
          data={[{
            x: stats.predictions_last_14_days.map((d) => d.date),
            y: stats.predictions_last_14_days.map((d) => d.count),
            type: 'bar',
            marker: { color: '#12877F' },
          }]}
          layout={barLayout('Predictions — last 14 days')}
          config={{ displayModeBar: false }}
          style={{ width: '100%' }}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border border-slate-200 rounded-xl p-4">
          <Plot
            data={[{
              x: stats.predictions_by_class.map((d) => d.label),
              y: stats.predictions_by_class.map((d) => d.count),
              type: 'bar',
              marker: { color: '#0B3B5C' },
            }]}
            layout={barLayout('Predictions by class')}
            config={{ displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
        <div className="bg-card border border-slate-200 rounded-xl p-4">
          <Plot
            data={[{
              x: stats.predictions_by_risk.map((d) => d.label),
              y: stats.predictions_by_risk.map((d) => d.count),
              type: 'bar',
              marker: { color: ['#B91C1C', '#B45309', '#15803D'] },
            }]}
            layout={barLayout('Predictions by risk level')}
            config={{ displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
        <div className="bg-card border border-slate-200 rounded-xl p-4">
          <Plot
            data={[{
              x: stats.users_by_role.map((d) => d.label),
              y: stats.users_by_role.map((d) => d.count),
              type: 'bar',
              marker: { color: '#12877F' },
            }]}
            layout={barLayout('Users by role')}
            config={{ displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </div>
  )
}

function MiniStat({ label, value }) {
  return (
    <div className="bg-card rounded-xl border border-slate-200 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500 font-medium">{label}</p>
      <p className="mt-1.5 text-2xl font-display font-semibold text-ink">{value}</p>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-slate-600 mb-1">{label}</span>
      {children}
    </label>
  )
}
