import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client.js'
import AppShell from '../components/AppShell.jsx'

const EMPTY = {
  patient_code: '', name: '', age: '', gender: '', blood_pressure: '',
  heart_rate: '', symptoms: '', doctor_name: '',
}

export default function Patients() {
  const [patients, setPatients] = useState([])
  const [query, setQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  function load(q = '') {
    client.get('/patients', { params: { q } }).then((r) => setPatients(r.data))
  }

  useEffect(() => { load() }, [])

  function onSearch(e) {
    e.preventDefault()
    load(query)
  }

  async function onCreate(e) {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const payload = { ...form, age: form.age ? Number(form.age) : null, heart_rate: form.heart_rate ? Number(form.heart_rate) : null }
      await client.post('/patients', payload)
      setForm(EMPTY)
      setShowForm(false)
      load(query)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save this patient.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppShell>
      <div className="p-8 max-w-6xl">
        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="font-display text-2xl font-semibold text-ink">Patients</h1>
            <p className="text-sm text-slate-500 mt-0.5">Register patients and open their ECG history</p>
          </div>
          <button onClick={() => setShowForm((s) => !s)}
                  className="bg-ink text-white text-sm rounded-lg px-4 py-2.5 hover:bg-ink/90">
            {showForm ? 'Cancel' : '+ New Patient'}
          </button>
        </header>

        {showForm && (
          <form onSubmit={onCreate} className="bg-card border border-slate-200 rounded-xl p-6 mb-8 grid grid-cols-2 md:grid-cols-4 gap-4">
            <Field label="Patient ID *"><input required value={form.patient_code}
              onChange={(e) => setForm({ ...form, patient_code: e.target.value })} className="input" /></Field>
            <Field label="Name *"><input required value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" /></Field>
            <Field label="Age"><input type="number" value={form.age}
              onChange={(e) => setForm({ ...form, age: e.target.value })} className="input" /></Field>
            <Field label="Gender">
              <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} className="input">
                <option value="">–</option><option>Male</option><option>Female</option><option>Other</option>
              </select>
            </Field>
            <Field label="Blood Pressure"><input placeholder="120/80" value={form.blood_pressure}
              onChange={(e) => setForm({ ...form, blood_pressure: e.target.value })} className="input" /></Field>
            <Field label="Heart Rate"><input type="number" value={form.heart_rate}
              onChange={(e) => setForm({ ...form, heart_rate: e.target.value })} className="input" /></Field>
            <Field label="Doctor Name"><input value={form.doctor_name}
              onChange={(e) => setForm({ ...form, doctor_name: e.target.value })} className="input" /></Field>
            <Field label="Symptoms" full><textarea value={form.symptoms} rows={2}
              onChange={(e) => setForm({ ...form, symptoms: e.target.value })} className="input" /></Field>

            {error && <p className="col-span-full text-sm text-risk-high">{error}</p>}
            <div className="col-span-full">
              <button disabled={saving} className="bg-tealline text-white text-sm rounded-lg px-5 py-2.5 hover:bg-tealline/90 disabled:opacity-60">
                {saving ? 'Saving…' : 'Save Patient'}
              </button>
            </div>
          </form>
        )}

        <form onSubmit={onSearch} className="mb-4 flex gap-2 max-w-sm">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by name or Patient ID"
                 className="input" />
          <button className="text-sm px-4 rounded-lg border border-slate-300 hover:border-ink">Search</button>
        </form>

        <div className="bg-card rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wide">
                <th className="px-5 py-2 font-medium">Patient ID</th>
                <th className="px-5 py-2 font-medium">Name</th>
                <th className="px-5 py-2 font-medium">Age / Gender</th>
                <th className="px-5 py-2 font-medium">Doctor</th>
                <th className="px-5 py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {patients.length === 0 && (
                <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">No patients found.</td></tr>
              )}
              {patients.map((p) => (
                <tr key={p.id} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-5 py-3 font-mono text-xs">{p.patient_code}</td>
                  <td className="px-5 py-3">{p.name}</td>
                  <td className="px-5 py-3 text-slate-500">{p.age || '–'} / {p.gender || '–'}</td>
                  <td className="px-5 py-3 text-slate-500">{p.doctor_name || '–'}</td>
                  <td className="px-5 py-3 text-right">
                    <Link to={`/patients/${p.patient_code}`} className="text-tealline text-xs hover:underline">Open →</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <style>{`.input { width:100%; border:1px solid #CBD5E1; border-radius:0.5rem; padding:0.5rem 0.7rem; font-size:0.85rem; background:white; }
                .input:focus { border-color:#12877F; outline:none; }`}</style>
    </AppShell>
  )
}

function Field({ label, children, full }) {
  return (
    <label className={`block ${full ? 'col-span-full' : ''}`}>
      <span className="block text-xs font-medium text-slate-600 mb-1">{label}</span>
      {children}
    </label>
  )
}
