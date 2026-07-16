import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import client from '../api/client.js'
import AppShell from '../components/AppShell.jsx'
import RiskBadge from '../components/RiskBadge.jsx'
import { formatLocalDateTime } from '../utils/time.js'
import ECGChart from '../components/ECGChart.jsx'
import SaliencyHeatmap from '../components/SaliencyHeatmap.jsx'
import ProcessingOverlay from '../components/ProcessingOverlay.jsx'

export default function PatientDetail() {
  const { code } = useParams()
  const [patient, setPatient] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [downloadingId, setDownloadingId] = useState(null)

  const [fileFormat, setFileFormat] = useState('csv')
  const [file, setFile] = useState(null)
  const [heaFile, setHeaFile] = useState(null)
  const [samplingRate, setSamplingRate] = useState(100)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)

  function loadAll() {
    client.get(`/patients/${code}`).then((r) => setPatient(r.data)).catch(() => setError('Patient not found.'))
    client.get(`/patients/${code}/history`).then((r) => setHistory(r.data)).catch(() => {})
  }

  useEffect(() => { loadAll() }, [code])

  async function onUpload(e) {
    e.preventDefault()
    setError('')
    if (!file) { setError('Choose an ECG file first.'); return }
    setUploading(true)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('patient_code', code)
      fd.append('file_format', fileFormat)
      fd.append('sampling_rate', samplingRate)
      fd.append('file', file)
      if (fileFormat === 'wfdb' && heaFile) fd.append('hea_file', heaFile)
      const { data } = await client.post('/ecg/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResult(data)
      loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed — check the file format matches your selection.')
    } finally {
      setUploading(false)
    }
  }

  async function downloadReport(recordId) {
    setError('')
    setDownloadingId(recordId)
    try {
      // NOTE: this endpoint requires a bearer token, so it must be fetched
      // through the authenticated axios client (a plain <a href> would hit
      // the API with no Authorization header and get a 401).
      const res = await client.get(`/ecg/record/${recordId}/report`, { responseType: 'blob' })
      const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = `ecg_report_${code}_${recordId}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      setError('Could not download the report — please try again.')
    } finally {
      setDownloadingId(null)
    }
  }

  if (!patient) {
    return <AppShell><div className="p-8 text-slate-500">{error || 'Loading…'}</div></AppShell>
  }

  return (
    <AppShell>
      <ProcessingOverlay active={uploading} />
      <div className="p-8 max-w-6xl space-y-8">
        <header className="flex items-start justify-between">
          <div>
            <p className="text-xs font-mono text-tealline">{patient.patient_code}</p>
            <h1 className="font-display text-2xl font-semibold text-ink">{patient.name}</h1>
            <p className="text-sm text-slate-500 mt-1">
              {patient.age || '–'} yrs · {patient.gender || '–'} · BP {patient.blood_pressure || '–'} · HR {patient.heart_rate || '–'} bpm
            </p>
            {patient.symptoms && <p className="text-sm text-slate-500 mt-1">Symptoms: {patient.symptoms}</p>}
          </div>
        </header>

        {/* Upload */}
        <section className="bg-card border border-slate-200 rounded-xl p-6">
          <h2 className="font-display font-semibold text-ink text-sm mb-4">Upload ECG</h2>
          <form onSubmit={onUpload} className="flex flex-wrap items-end gap-4">
            <label className="block">
              <span className="block text-xs font-medium text-slate-600 mb-1">Format</span>
              <select value={fileFormat} onChange={(e) => setFileFormat(e.target.value)} className="input w-32">
                <option value="csv">CSV</option>
                <option value="npy">NPY</option>
                <option value="mat">MAT</option>
                <option value="wfdb">WFDB</option>
              </select>
            </label>
            <label className="block">
              <span className="block text-xs font-medium text-slate-600 mb-1">Sampling rate (Hz)</span>
              <input type="number" value={samplingRate} onChange={(e) => setSamplingRate(e.target.value)} className="input w-32" />
            </label>
            <label className="block">
              <span className="block text-xs font-medium text-slate-600 mb-1">
                {fileFormat === 'wfdb' ? 'Record (.dat)' : `ECG file (.${fileFormat})`}
              </span>
              <input type="file" onChange={(e) => setFile(e.target.files[0])} className="text-sm" />
            </label>
            {fileFormat === 'wfdb' && (
              <label className="block">
                <span className="block text-xs font-medium text-slate-600 mb-1">Header (.hea)</span>
                <input type="file" onChange={(e) => setHeaFile(e.target.files[0])} className="text-sm" />
              </label>
            )}
            <button disabled={uploading} className="bg-ink text-white text-sm rounded-lg px-5 py-2.5 hover:bg-ink/90 disabled:opacity-60">
              {uploading ? 'Processing…' : 'Upload & Predict'}
            </button>
          </form>
          {error && <p className="text-sm text-risk-high mt-3">{error}</p>}
        </section>

        {/* Live result */}
        {result && <PredictionPanel result={result} />}

        {/* History */}
        <section>
          <h2 className="font-display font-semibold text-ink text-sm mb-3">Previous History</h2>
          {history.length === 0 && <p className="text-sm text-slate-400">No previous ECG records.</p>}
          <div className="space-y-2">
            {history.map((rec) => (
              <div key={rec.id} className="bg-card border border-slate-200 rounded-lg px-5 py-3 flex items-center justify-between text-sm">
                <div className="flex items-center gap-4">
                  <span className="text-slate-500 font-mono text-xs">
                    {formatLocalDateTime(rec.uploaded_at)}
                  </span>
                  <span className="font-medium text-ink">{rec.prediction?.top_class || '—'}</span>
                  {rec.prediction && <RiskBadge level={rec.prediction.risk_level} />}
                  {rec.prediction && (
                    <span className="text-slate-500 font-mono text-xs">
                      {(rec.prediction.top_confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                {rec.prediction && (
                  <button type="button" className="text-tealline text-xs hover:underline disabled:opacity-50"
                          disabled={downloadingId === rec.id}
                          onClick={() => downloadReport(rec.id)}>
                    {downloadingId === rec.id ? 'Downloading…' : 'Download report →'}
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
      <style>{`.input { border:1px solid #CBD5E1; border-radius:0.5rem; padding:0.5rem 0.7rem; font-size:0.85rem; background:white; }
                .input:focus { border-color:#12877F; outline:none; }`}</style>
    </AppShell>
  )
}

function PredictionPanel({ result }) {
  const p = result.prediction
  const probs = Object.entries(p.probs).sort((a, b) => b[1] - a[1])

  return (
    <section className="bg-card border border-slate-200 rounded-xl p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="font-display font-semibold text-ink text-sm">Prediction</h2>
          <p className="text-xl font-display font-semibold text-ink mt-1">{diagnosisLabel(p.top_class)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Confidence</p>
          <p className="text-2xl font-mono font-semibold text-ink">{(p.top_confidence * 100).toFixed(1)}%</p>
          <div className="mt-1"><RiskBadge level={p.risk_level} size="lg" /></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
        <div className="md:col-span-2 space-y-2">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Detected Classes</p>
          {probs.map(([cls, prob]) => (
            <div key={cls} className="flex items-center gap-2 text-sm">
              <span className={p.predicted_classes.includes(cls) ? 'text-tealline' : 'text-slate-300'}>
                {p.predicted_classes.includes(cls) ? '✔' : '✖'}
              </span>
              <span className="w-14 font-mono text-xs">{cls}</span>
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-ink" style={{ width: `${prob * 100}%` }} />
              </div>
              <span className="w-12 text-right font-mono text-xs text-slate-500">{(prob * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>

        <div className="md:col-span-3 bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900">
          <p className="font-medium mb-1">Model Interpretation</p>
          <p>
            The model detected patterns consistent with <b>{diagnosisLabel(p.top_class)}</b> at{' '}
            {(p.top_confidence * 100).toFixed(1)}% confidence. Highlighted ECG regions below indicate the
            segments that contributed most strongly to this prediction — not a confirmed lesion location.
          </p>
          <p className="mt-2 font-medium">
            Suggested action: {p.risk_level === 'HIGH' ? 'Immediate cardiology review recommended.' : 'Routine clinical correlation recommended.'}
          </p>
        </div>
      </div>

      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">ECG Viewer</p>
      <ECGChart rawSignal={result.raw_signal} saliency={result.saliency_timeseries} />

      <div className="mt-5">
        <SaliencyHeatmap saliency={result.saliency_timeseries} />
      </div>

      <p className="text-[11px] text-slate-400 mt-4 border-t border-slate-100 pt-3">
        This output is generated by an AI decision-support tool (MSCMA-Net) and is intended to assist,
        not replace, clinical judgment. All findings must be reviewed and confirmed by a qualified
        clinician before any care decision.
      </p>
    </section>
  )
}

const LABELS = {
  NORM: 'Normal ECG',
  MI: 'Acute Myocardial Infarction',
  STTC: 'ST/T Wave Change',
  CD: 'Conduction Disturbance',
  HYP: 'Hypertrophy',
}
function diagnosisLabel(cls) {
  return LABELS[cls] || cls
}
