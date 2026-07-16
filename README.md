# ECG-MSCMA-Net — Clinical Decision Support System

An AI-powered ECG classification app built around **MSCMA-Net** (Multi-Scale Convolutional + Multi-head Attention Network). It classifies 12-lead ECG signals into 5 diagnostic categories, generates explainability heatmaps, and produces downloadable clinical PDF reports — wrapped in a full-stack web app with role-based logins (admin, doctor, cardiologist, nurse).

> ⚠️ **Disclaimer:** This is a decision-support demo, not a certified medical device. All predictions must be reviewed and confirmed by a qualified clinician before any care decision.

## Features

- 🫀 12-lead ECG classification into **NORM, MI, STTC, CD, HYP**
- 🔥 Grad×Input saliency heatmaps showing which leads/regions drove a prediction
- 📄 Auto-generated PDF clinical reports per ECG record
- 👥 Role-based auth (JWT) — admin / doctor / cardiologist / nurse
- 📊 Patient dashboard with ECG upload history
- 📥 Accepts `.csv`, `.npy`, and `.wfdb` (`.dat` + `.hea`) ECG formats at any sampling rate

## Tech Stack

**Backend:** FastAPI, PyTorch, SQLAlchemy (SQLite by default), JWT auth (bcrypt-hashed passwords)
**Frontend:** React 18 + Vite, Tailwind CSS, Plotly.js (signal/saliency charts), React Router, Axios

## Project Structure

```
ecg-mscma-app/
├── README.md
├── CHANGES.md
├── QUICKSTART.md
├── LICENSE
├── .gitignore
│
├── backend/
│   ├── app.py                   # FastAPI entrypoint
│   ├── auth.py                  # JWT auth logic
│   ├── config.py                # Env config, classes, disclaimer text
│   ├── database.py               # DB session/engine setup
│   ├── models_db.py              # SQLAlchemy ORM models
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── model.py                  # MSCMA-Net architecture
│   ├── predict.py                # Inference + saliency service
│   ├── preprocessing.py          # Signal loading/resampling (csv/npy/wfdb)
│   ├── reports.py                # PDF report generation
│   ├── seed.py                   # Creates DB + demo accounts
│   ├── check_checkpoint.py       # Utility to inspect a saved checkpoint
│   ├── requirements.txt
│   ├── README.md                 # Backend-specific setup docs
│   │
│   ├── routers/
│   │   ├── auth_router.py        # Login/token endpoints
│   │   ├── patients_router.py    # Patient CRUD + dashboard stats
│   │   ├── ecg_router.py         # ECG upload/predict/history/report
│   │   └── admin_router.py       # Admin-only user management
│   │
│   ├── weights/                  # Trained checkpoint goes here (gitignored)
│   ├── database/                 # SQLite file lives here (gitignored)
│   ├── uploads/                  # Uploaded ECG files (gitignored)
│   └── reports_out/              # Generated PDF/heatmap outputs (gitignored)
│
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    ├── README.md
    │
    └── src/
        ├── main.jsx
        ├── App.jsx
        │
        ├── api/
        │   └── client.js         # Axios instance + auth interceptor
        │
        ├── context/
        │   └── AuthContext.jsx   # Auth state/provider
        │
        ├── components/
        │   ├── AppShell.jsx
        │   ├── ProtectedRoute.jsx
        │   ├── AdminRoute.jsx
        │   ├── ECGChart.jsx
        │   ├── SaliencyHeatmap.jsx
        │   ├── RiskBadge.jsx
        │   ├── StatCard.jsx
        │   └── ProcessingOverlay.jsx
        │
        ├── pages/
        │   ├── Login.jsx
        │   ├── Dashboard.jsx
        │   ├── Patients.jsx
        │   ├── PatientDetail.jsx
        │   └── Admin.jsx
        │
        ├── utils/
        │   └── time.js
        │
        └── styles/
            └── index.css
```

`backend/weights/`, `backend/database/`, `backend/uploads/`, and `backend/reports_out/` exist locally but their contents are gitignored (except `.gitkeep` placeholders) — they'll appear empty or missing on GitHub until someone adds real files.

## Getting Started

### Prerequisites
- Python 3.10+ (tested on 3.13)
- Node.js 18+
- A trained MSCMA-Net checkpoint (see `backend/README.md` for the exact format)

### 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Add your trained checkpoint to `backend/weights/best_model.pth` (see `backend/README.md` for the required checkpoint format — `model_state`, `lead_mean`, `lead_std`, optional `thresholds`).

Create a `backend/.env` file (see the Configuration section below for the required variables) and set `SECRET_KEY` to a long random string.

Create the database and demo accounts:

```bash
python seed.py
```

Run the API:

```bash
uvicorn app:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

App runs at http://localhost:5173 and talks to the backend at `http://localhost:8000`.

### Demo logins

| Username | Password   | Role         |
|----------|------------|--------------|
| admin    | admin123   | admin        |
| doctor   | doctor123  | doctor       |
| cardio   | cardio123  | cardiologist |
| nurse    | nurse123   | nurse        |

⚠️ Change or remove these before deploying anywhere real.

## Configuration

Create a `backend/.env` file with these variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret — set to a long random string |
| `DATABASE_URL` | Defaults to local SQLite; swap for Postgres in production |
| `MODEL_CHECKPOINT` | Path to the `.pth` checkpoint served for inference |
| `N_LEADS` / `SEQ_LEN` | Must match your training run (default 12 leads, 1000 samples) |
| `CLASSES` | Comma-separated class labels (default `NORM,MI,STTC,CD,HYP`) |

## Notes Before Production Use

- No rate limiting, refresh tokens, or audit logging yet — add these before handling real patient health information.
- SQLite is fine for a demo; use Postgres for multi-user/production deployments.
- The saliency heatmap is a Grad×Input map computed at request time, not the model's internal attention weights — the UI already discloses this.
- Passwords are bcrypt-hashed; `requirements.txt` deliberately pins `bcrypt==4.0.1` for compatibility with `passlib`.

## Contributing

1. Fork or clone the repo
2. Create a feature branch: `git checkout -b feature/your-change`
3. Commit your changes and push: `git push -u origin feature/your-change`
4. Open a Pull Request

Please don't commit `.env`, database files (`*.db`), model weights, or `node_modules` — these are excluded via `.gitignore`.

## License

This project is licensed under the [MIT License](LICENSE) — see the LICENSE file for details.
