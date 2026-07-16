<<<<<<< HEAD
# ECG Clinical Decision Support System — MSCMA-Net

A full-stack demo app around your trained MSCMA-Net checkpoint: FastAPI
backend + React frontend, matching the workflow you sketched:

```
Doctor Login → Dashboard → Register/Select Patient → Upload ECG →
Preprocessing → MSCMA-Net Prediction → Results + Confidence + Heatmap →
Save to Database → Generate PDF Report → Retrieve by Patient ID
```

## Project layout

```
ecg-mscma-app/
├── backend/            FastAPI app, model, DB, PDF report generation
│   ├── app.py
│   ├── model.py         MSCMA-Net architecture (must match your training code)
│   ├── predict.py       loads checkpoint once, runs inference + saliency
│   ├── preprocessing.py CSV / NPY / WFDB loaders + normalization
│   ├── reports.py       PDF report builder
│   ├── routers/         auth, patients, ecg upload/predict
│   ├── weights/         <- put your best_model.pth here
│   └── README.md        full backend setup instructions
└── frontend/            React + Vite + Tailwind + Plotly
    ├── src/pages/        Login, Dashboard, Patients, PatientDetail
    ├── src/components/   AppShell, ECGChart, RiskBadge, ProcessingOverlay…
    └── README.md         full frontend setup instructions
```

## Quickest path to a working demo

```bash
# 1) backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # edit SECRET_KEY etc.
cp /path/to/your/best_model.pth weights/   # your trained MSCMA-Net checkpoint
python seed.py                            # creates DB + demo logins
uvicorn app:app --reload --port 8000

# 2) frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Then open http://localhost:5173, log in with `doctor` / `doctor123`, register
a patient, and upload a CSV/NPY/WFDB ECG file to see a live prediction.

## What's implemented vs. simplified (read before your demo/viva)

**Implemented end-to-end:**
- Role-based login (JWT + bcrypt), 4 demo roles
- Dashboard stats (today's patients / predictions / high-risk / normal)
- Patient registration + search + per-patient history
- ECG upload (CSV, NPY, WFDB) → preprocessing → MSCMA-Net inference
- Prediction screen: per-class probabilities, confidence, risk level,
  detected classes, ECG viewer with a saliency (Grad×Input) overlay per lead
- PDF report generation and download, with hospital name, patient details,
  prediction table, interpretation, disclaimer
- History of previous visits per patient

**Deliberately simplified (call these out if asked in a review):**
- The "heatmap" is a Grad×Input saliency map computed at request time, not
  the model's internal attention weights and not a validated clinical
  localization — the UI already says this explicitly, keep that wording.
- No admin panel UI yet (the API supports creating users via
  `POST /auth/users` as an admin, but there's no screen for it — easy to add
  as `frontend/src/pages/Admin.jsx` following the `Patients.jsx` pattern).
- SQLite + local file storage — fine for a project demo, swap for
  Postgres + S3-style storage before anything resembling production.
- Auth is JWT + bcrypt but has no rate limiting, refresh tokens, or audit
  trail — call this out as "future work" rather than presenting it as
  production-grade security.

## If your checkpoint differs from what's expected

`backend/model.py` is copied *exactly* from your training notebook. If you
changed the architecture since training, this will fail to load with a
`state_dict` key-mismatch error — copy the current `MultiScaleCNNMambaAttnNet`
(and any blocks it depends on) from your latest notebook into `model.py`
before running.

If your checkpoint doesn't include `lead_mean`/`lead_std`/`thresholds`
(the notebook's `CKPT_PATH` save does include them), predictions will run but
use un-normalized inputs and a flat 0.5 threshold — add those keys to your
`torch.save(...)` call, or hardcode them in `predict.py`.
=======
# Major-Project-ECG-MSCMA-APP-
>>>>>>> 11dad9c35eac3ed457e6184691ae4ac57a0945d8
