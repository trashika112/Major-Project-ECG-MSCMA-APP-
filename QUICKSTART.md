# Quickstart (Windows / PowerShell)

This covers the exact setup that was verified to work, including fixes for
errors commonly hit on Windows + Python 3.13.

## 1. Save your checkpoint with tuned thresholds

In your training notebook, after your evaluation cell has run (so `val_probs`
/ `val_targets` exist), run a cell like this **once** before downloading the
checkpoint:

```python
import os, numpy as np, torch
from sklearn.metrics import f1_score

DEPLOY_CKPT_PATH = os.path.join(CACHE_DIR, 'best_mscma_net_main.pt')

tuned_thresholds = np.zeros(N_CLASSES, dtype=np.float32)
for i in range(N_CLASSES):
    best_th, best_f1 = 0.5, -1
    for th in np.arange(0.05, 0.96, 0.01):
        f1 = f1_score(val_targets[:, i], (val_probs[:, i] >= th).astype(int), zero_division=0)
        if f1 > best_f1:
            best_f1, best_th = f1, th
    tuned_thresholds[i] = best_th

ckpt = torch.load(DEPLOY_CKPT_PATH, map_location='cpu', weights_only=False)
ckpt['thresholds'] = tuned_thresholds
torch.save(ckpt, DEPLOY_CKPT_PATH)
```

Without this, the app silently uses a flat 0.5 threshold for every class
instead of your validated per-class thresholds.

## 2. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Copy your checkpoint into `weights/`, then **edit `.env`** so
`MODEL_CHECKPOINT` matches the exact filename you used (`.pt` and `.pth` both
work — torch doesn't care about the extension):

```
MODEL_CHECKPOINT=weights/best_model.pt
```

```powershell
python seed.py
python -m uvicorn app:app --reload --port 8000
```

Confirm the console prints `[ModelService] Loaded checkpoint: weights/best_model.pt`
— if it prints a `WARNING: checkpoint not found` instead, the `.env` path
doesn't match your actual file.

## 3. Frontend (new terminal)

```powershell
cd frontend
```

If `npm` is blocked by PowerShell's script execution policy, run once (as your
own user, no admin needed):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

```powershell
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`).

## Notes

- `requirements.txt` pins `numpy>=2.1.0` / `scipy>=1.14.1` (not the original
  `numpy==1.26.4` / `scipy==1.13.1`) because those older pins have no
  prebuilt wheel for Python 3.13 and fail to build from source on a typical
  Windows machine (missing OpenBLAS). If you're on Python 3.11/3.12 instead,
  either pin still works.
- `backend/model.py` was verified parameter-for-parameter (identical keys,
  shapes, and forward-pass outputs) against the training notebook's
  architecture — a checkpoint from the notebook loads here with zero
  mismatches.
- `MODEL_CHECKPOINT_ALT` in `.env` is currently unused by `predict.py` — only
  `MODEL_CHECKPOINT` is loaded. The deployed app therefore runs single-model
  inference; your notebook's *reported* paper metrics use a best+SWA
  checkpoint ensemble, so live predictions may be marginally different from
  the exact numbers in your report.
