# ECG-MSCMA-Net Frontend (React + Vite + Tailwind)

## 1. Install

Requires Node.js 18+.

```bash
cd frontend
npm install
```

## 2. Point it at your backend (optional)

By default the app calls `http://localhost:8000`. To change that, create a
`.env` file:

```
VITE_API_BASE=http://localhost:8000
```

## 3. Run

```bash
npm run dev
```

Open http://localhost:5173 — make sure the backend (`uvicorn app:app --reload
--port 8000`) is running first, and that you've run `python seed.py` in the
backend so there's at least one login.

## Pages included

- **Login** — role-based login (doctor / cardiologist / nurse / admin)
- **Dashboard** — today's patients, predictions, high-risk cases, normal ECGs
- **Patients** — register a patient, search, open a patient's record
- **Patient detail** — upload an ECG (CSV / NPY / WFDB), see the live
  prediction (confidence, risk level, detected classes, per-lead ECG viewer
  with a Grad×Input saliency overlay), download a PDF report, and browse
  previous visits

## Build for production

```bash
npm run build
npm run preview   # sanity-check the production build locally
```

Deploy the `dist/` folder to any static host (Nginx, Vercel, Netlify, etc.)
and point `VITE_API_BASE` at your deployed FastAPI URL.
