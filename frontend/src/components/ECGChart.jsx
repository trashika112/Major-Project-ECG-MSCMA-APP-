import React, { useState, useMemo } from 'react'
import Plotly from 'plotly.js-basic-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'

const Plot = createPlotlyComponent(Plotly)

const LEAD_NAMES = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

/**
 * rawSignal: number[][]  shape (T, leads) as returned by /ecg/upload
 * saliency: number[][]   shape (leads, T) — abs(grad * input), higher = more influential
 */
export default function ECGChart({ rawSignal, saliency }) {
  const leads = rawSignal?.[0]?.length || 12
  const [activeLead, setActiveLead] = useState(0)
  const leadCount = Math.min(leads, LEAD_NAMES.length)

  const t = useMemo(() => rawSignal.map((_, i) => i), [rawSignal])
  const y = useMemo(() => rawSignal.map((row) => row[activeLead]), [rawSignal, activeLead])
  const sal = useMemo(() => saliency?.[activeLead] || [], [saliency, activeLead])

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {Array.from({ length: leadCount }).map((_, i) => (
          <button
            key={i}
            onClick={() => setActiveLead(i)}
            className={`px-2.5 py-1 text-xs font-mono rounded-md border transition-colors ${
              activeLead === i
                ? 'bg-ink text-white border-ink'
                : 'bg-white text-slate-600 border-slate-300 hover:border-ink'
            }`}
          >
            {LEAD_NAMES[i] || `L${i + 1}`}
          </button>
        ))}
      </div>

      <Plot
        data={[
          {
            x: t,
            y,
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#0B3B5C', width: 1.4 },
            marker: sal.length
              ? {
                  size: 3,
                  color: sal,
                  colorscale: [[0, 'rgba(18,135,127,0.05)'], [1, 'rgba(185,28,28,0.9)']],
                  showscale: true,
                  colorbar: { title: 'Saliency', titleside: 'right', thickness: 12, len: 0.7 },
                }
              : { size: 0 },
            hovertemplate: 'sample %{x}<br>amplitude %{y:.3f}<extra></extra>',
          },
        ]}
        layout={{
          height: 320,
          margin: { l: 45, r: 20, t: 10, b: 35 },
          xaxis: { title: 'Sample (10s record)', showgrid: false, zeroline: false },
          yaxis: { title: 'mV (normalized)', showgrid: true, gridcolor: '#EEF2F6', zeroline: false },
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          font: { family: 'Inter, sans-serif', size: 11, color: '#334155' },
          dragmode: 'pan',
        }}
        config={{ displayModeBar: true, scrollZoom: true, displaylogo: false,
                  modeBarButtonsToRemove: ['lasso2d', 'select2d'] }}
        style={{ width: '100%' }}
      />
      <p className="text-[11px] text-slate-500 mt-1">
        Scroll to zoom, drag to pan. Point color shows how strongly that region contributed to the
        model's top prediction (Grad×Input saliency) — not a clinical annotation.
      </p>
    </div>
  )
}
