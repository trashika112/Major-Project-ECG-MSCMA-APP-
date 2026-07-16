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
├── backend/
│   ├── app.py              # FastAPI entrypoint
│   ├── model.py             # MSCMA-Net architecture
│   ├── predict.py           # Inference + saliency service
│   ├── preprocessing.py     # Signal loading/resampling (csv/npy/wfdb)
│   ├── reports.py           # PDF report generation
│   ├── routers/              # auth / patients / ecg / admin endpoints
│   ├── weights/              # trained checkpoint goes here (not committed)
│   └── requirements.txt
└── frontend/
    ├── src/
    ├── package.json
    └── vite.config.js
```

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

```bash
cp .env.example .env
# edit .env: set SECRET_KEY to a long random string
```

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

Key variables in `backend/.env` (copy from `.env.example`):

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
