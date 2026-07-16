# ECG-MSCMA-Net Backend (FastAPI)

## 1. Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If you have a GPU and want CUDA-accelerated inference, install the matching
torch build from https://pytorch.org/get-started/locally/ instead of the
plain `pip install torch` that requirements.txt pulls in.

## 2. Add your trained model

Copy your checkpoint(s) into `backend/weights/`:

```
backend/weights/best_model.pth        # <- the one served in production (required)
backend/weights/best_model_swa.pth    # optional, not loaded by default
```

The checkpoint must be a `torch.save(...)` dict that includes at least:
```python
{'model_state': model.state_dict(),
 'lead_mean': lead_mean,     # from your training notebook, shape (12,)
 'lead_std':  lead_std,      # from your training notebook, shape (12,)
 # optional:
 'thresholds': thresholds}   # F1-tuned per-class thresholds, shape (5,)
```
This is exactly what `main_model_mscma_net_final.ipynb` already saves for
`CKPT_PATH` / `SWA_CKPT_PATH`, so you can copy those files directly.

If your checkpoint has a different filename, either rename it to
`best_model.pth` or set `MODEL_CHECKPOINT=weights/<your-file>.pth` in `.env`.

## 3. Configure

```bash
cp .env.example .env
# edit .env: set SECRET_KEY to a long random string, double check
# MODEL_CHECKPOINT / N_LEADS / SEQ_LEN / CLASSES match your training run
```

## 4. Create the database + default logins

```bash
python seed.py
```

This creates `database/patients.db` (SQLite) and 4 demo accounts:

| Username | Password   | Role         |
|----------|------------|--------------|
| admin    | admin123   | admin        |
| doctor   | doctor123  | doctor       |
| cardio   | cardio123  | cardiologist |
| nurse    | nurse123   | nurse        |

**Change these before deploying anywhere real** — create real users via
`POST /auth/users` (admin-only) and disable/delete the demo ones.

## 5. Run

```bash
uvicorn app:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check (confirms the checkpoint loaded): http://localhost:8000/health

## Supported ECG upload formats

| Format | What to upload | Expected shape |
|---|---|---|
| `csv`  | one `.csv` file | 12 columns x N rows, or 12 rows x N columns (auto-detected) |
| `npy`  | one `.npy` file | `(12, T)` or `(T, 12)` numpy array |
| `wfdb` | a `.dat` **and** a `.hea` file (same base name) | standard PhysioNet WFDB record |

Any sampling rate is accepted — the signal is resampled to the model's fixed
input length (`SEQ_LEN`, default 1000 = 10s @ 100Hz) before inference.

## Notes / things to harden before real deployment

- Passwords are bcrypt-hashed and auth uses JWT, but there's no rate limiting,
  refresh tokens, or audit logging yet — add these before handling real PHI.
- SQLite is fine for a demo; switch `DATABASE_URL` to Postgres for anything
  multi-user or production-like.
- The "explainability" heatmap is a Grad×Input saliency map computed at
  request time (not the model's internal attention weights) — good enough to
  show *which leads/regions mattered*, but say so explicitly in the UI, which
  the frontend already does.
- This is a decision-support demo, not a certified medical device — keep the
  disclaimer visible everywhere a prediction is shown (already wired into
  both the API responses and the PDF report).
