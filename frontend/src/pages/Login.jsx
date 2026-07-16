import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('doctor')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password, role)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid login. Check your username, password, and role.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-ink relative overflow-hidden">
      <ECGBackdrop />
      <div className="m-auto w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-white">
            <PulseMark />
            <span className="font-display text-xl font-semibold tracking-tight">ECG Clinical Decision Support</span>
          </div>
          <p className="text-white/50 text-sm mt-1 font-mono">MSCMA-Net-assisted 12-lead ECG triage</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-2xl p-8 space-y-5">
          <h1 className="font-display font-semibold text-lg text-ink">Hospital Login</h1>

          <Field label="Username">
            <input value={username} onChange={(e) => setUsername(e.target.value)} required
                   className="input" placeholder="e.g. doctor" autoFocus />
          </Field>

          <Field label="Password">
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                   className="input" placeholder="••••••••" />
          </Field>

          <Field label="Role">
            <select value={role} onChange={(e) => setRole(e.target.value)} className="input">
              <option value="doctor">Doctor</option>
              <option value="cardiologist">Cardiologist</option>
              <option value="nurse">Nurse</option>
              <option value="admin">Admin</option>
            </select>
          </Field>

          {error && <p className="text-sm text-risk-high bg-risk-high/10 rounded-lg px-3 py-2">{error}</p>}

          <button disabled={loading} type="submit"
                  className="w-full bg-ink hover:bg-ink/90 disabled:opacity-60 text-white rounded-lg py-2.5 font-medium transition-colors">
            {loading ? 'Signing in…' : 'Log In'}
          </button>

          <p className="text-[11px] text-slate-400 text-center pt-1">
            Demo logins: doctor/doctor123 &middot; cardio/cardio123 &middot; nurse/nurse123 &middot; admin/admin123
          </p>
        </form>
      </div>

      <style>{`.input { width:100%; border:1px solid #CBD5E1; border-radius:0.5rem; padding:0.55rem 0.75rem; font-size:0.9rem; }
                .input:focus { border-color:#12877F; }`}</style>
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

function PulseMark() {
  return (
    <svg width="24" height="24" viewBox="0 0 22 22" fill="none">
      <path d="M1 11h4l2-7 4 14 3-11 2 4h5" stroke="#12877F" strokeWidth="1.8"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ECGBackdrop() {
  // A faint, oversized ECG trace running across the login background — the
  // one signature visual moment on an otherwise quiet screen.
  return (
    <svg className="absolute inset-0 w-full h-full opacity-[0.10]" viewBox="0 0 1200 800" preserveAspectRatio="none">
      <path
        d="M0,400 L150,400 L180,320 L210,480 L240,120 L270,650 L300,400 L500,400 L530,340 L560,460 L590,400 L900,400 L930,300 L960,500 L990,180 L1020,620 L1050,400 L1200,400"
        stroke="#12877F" strokeWidth="3" fill="none" vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}
