import React, { useMemo } from 'react'
import Plotly from 'plotly.js-basic-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'

const Plot = createPlotlyComponent(Plotly)

const LEAD_NAMES = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

/**
 * saliency: number[][]  shape (leads, T) — abs(grad * input), higher = more influential.
 * Renders a Grad-CAM-style attention heatmap across all 12 leads at once, instead of
 * one lead at a time. This is the closest 1D-signal equivalent of an image Grad-CAM
 * overlay: ECG has no 2D spatial structure, so "attention" is shown as a lead x time
 * grid rather than a pixel heatmap.
 */
export default function SaliencyHeatmap({ saliency }) {
  const leadCount = Math.min(saliency?.length || 0, LEAD_NAMES.length)

  const z = useMemo(() => (saliency || []).slice(0, leadCount), [saliency, leadCount])
  const yLabels = useMemo(() => LEAD_NAMES.slice(0, leadCount), [leadCount])

  if (!z.length) return null

  return (
    <div className="bg-ink rounded-xl p-5">
      <div className="flex items-center justify-between mb-1">
        <p className="text-sm font-medium text-white">Model Attention Map</p>
        <span className="text-[10px] text-white/40 font-mono">Grad×Input saliency</span>
      </div>
      <p className="text-[11px] text-white/50 mb-3">
        Which lead and time-region most influenced the model's prediction — the ECG equivalent of a
        Grad-CAM heatmap, shown across all 12 leads simultaneously.
      </p>

      <Plot
        data={[
          {
            z,
            y: yLabels,
            type: 'heatmap',
            colorscale: [
              [0, '#0B1224'],
              [0.25, '#1E3A8A'],
              [0.5, '#0891B2'],
              [0.7, '#FACC15'],
              [1, '#DC2626'],
            ],
            showscale: false,
            hovertemplate: 'lead %{y}<br>sample %{x}<br>attention %{z:.2f}<extra></extra>',
          },
        ]}
        layout={{
          height: 34 * leadCount + 60,
          margin: { l: 40, r: 10, t: 6, b: 30 },
          xaxis: { title: 'Sample (10s record)', showgrid: false, color: '#94A3B8', tickfont: { size: 9 } },
          yaxis: { showgrid: false, color: '#CBD5E1', tickfont: { size: 10, family: 'monospace' }, autorange: 'reversed' },
          plot_bgcolor: '#0B1224',
          paper_bgcolor: 'transparent',
          font: { family: 'Inter, sans-serif', size: 10 },
        }}
        config={{ displayModeBar: false }}
        style={{ width: '100%' }}
      />

      <div className="flex items-center gap-2 mt-3">
        <span className="text-[10px] text-white/50">Low Attention</span>
        <div
          className="flex-1 h-1.5 rounded-full"
          style={{ background: 'linear-gradient(90deg, #0B1224, #1E3A8A, #0891B2, #FACC15, #DC2626)' }}
        />
        <span className="text-[10px] text-white/50">High Attention</span>
      </div>
    </div>
  )
}
