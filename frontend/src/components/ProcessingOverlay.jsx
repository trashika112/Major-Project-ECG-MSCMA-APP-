import React, { useEffect, useRef, useState } from 'react'

const STEPS = [
  'Uploading ECG',
  'Preprocessing signal',
  'Running MSCMA-Net',
  'Generating report',
]

/**
 * `active` = true for the entire duration of the real upload+predict request.
 *
 * Ticks are driven by two things working together, not a disconnected timer:
 *   1. While the real request is still in flight, we advance through the
 *      steps on a short timer, but DELIBERATELY STOP one step short of the
 *      end — so it never falsely claims to be "done" before the real work is.
 *   2. The moment the real request actually finishes (`active` flips back to
 *      false), we immediately flash through any remaining steps in quick
 *      succession so the user sees every tick complete, then close the
 *      overlay a beat later. This means a fast request (under a second)
 *      still shows all 4 steps ticking, and a slow request never lies about
 *      being further along than it really is.
 */
export default function ProcessingOverlay({ active }) {
  const [stepIdx, setStepIdx] = useState(0)
  const [visible, setVisible] = useState(false)
  const wasActive = useRef(false)

  useEffect(() => {
    if (active) {
      setVisible(true)
      setStepIdx(0)
      wasActive.current = true

      const id = setInterval(() => {
        setStepIdx((i) => (i < STEPS.length - 2 ? i + 1 : i)) // stop one short of the end
      }, 550)
      return () => clearInterval(id)
    }

    if (!active && wasActive.current) {
      wasActive.current = false
      let i = 0
      const finishId = setInterval(() => {
        setStepIdx((prev) => Math.min(prev + 1, STEPS.length - 1))
        i += 1
        if (i >= STEPS.length) clearInterval(finishId)
      }, 150)

      const closeId = setTimeout(() => setVisible(false), STEPS.length * 150 + 350)
      return () => { clearInterval(finishId); clearTimeout(closeId) }
    }
  }, [active])

  if (!visible) return null

  const allDone = stepIdx >= STEPS.length - 1 && !active

  return (
    <div className="fixed inset-0 bg-ink/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl px-8 py-7 w-full max-w-sm shadow-xl">
        <p className="font-display font-semibold text-ink mb-5">
          {allDone ? 'Done' : 'Processing ECG…'}
        </p>
        <ol className="space-y-3">
          {STEPS.map((label, i) => {
            const done = i < stepIdx || (allDone && i <= stepIdx)
            const current = !allDone && i === stepIdx
            return (
              <li key={label} className="flex items-center gap-3 text-sm">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono border transition-colors ${
                    done
                      ? 'bg-tealline border-tealline text-white'
                      : current
                      ? 'border-tealline text-tealline pulse-dot'
                      : 'border-slate-300 text-slate-300'
                  }`}
                >
                  {done ? '✓' : i + 1}
                </span>
                <span className={done || current ? 'text-slate-800' : 'text-slate-400'}>{label}</span>
              </li>
            )
          })}
        </ol>
      </div>
    </div>
  )
}
