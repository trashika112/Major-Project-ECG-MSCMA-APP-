# Changes in this update

## 0. Bug fixes (found via full end-to-end testing)

**Bug A — ECG/saliency chart was always empty right after upload.**
`POST /ecg/upload` builds a response dict that includes `raw_signal`,
`saliency_timeseries`, and `classes`, but the route declared
`response_model=schemas.ECGRecordOut`, which didn't list those fields.
FastAPI silently strips any field not declared on the response model, so the
frontend's `<ECGChart rawSignal={result.raw_signal} .../>` always received
`undefined`.
- Fix: `backend/schemas.py` — added `raw_signal`, `saliency_timeseries`,
  `classes` as optional fields on `ECGRecordOut` (they stay `null` on
  `/patients/{code}/history`, which reuses the same schema, since that
  endpoint never sets them).

**Bug B — "Download report" link 401'd in the browser.**
`GET /ecg/record/{id}/report` requires a bearer token, but the frontend
linked to it with a plain `<a href=... target="_blank">`. A raw anchor
navigation never carries the axios interceptor's `Authorization` header, so
the browser always got a 401.
- Fix: `frontend/src/pages/PatientDetail.jsx` — replaced the anchor with a
  button that fetches the PDF via the authenticated axios client
  (`responseType: 'blob'`) and triggers the download from an object URL.

**Note (not a bug, just fragile):** `backend/requirements.txt` pins
`bcrypt==4.0.1` deliberately — `passlib==1.7.4` (unmaintained) breaks with
`bcrypt>=4.1` (raises `ValueError` on hash instead of the old silent
72-byte truncation). Always install from the pinned `requirements.txt`
rather than `pip install passlib bcrypt` unpinned.

## 1. MAT file support (closes gap #1)
- `backend/preprocessing.py`: new `load_mat()` using `scipy.io.loadmat`. Looks for
  common signal variable names first (`val`, `signal`, `ecg`, `data`, `X`, `x` —
  `val` covers PhysioNet-style exports), then falls back to the largest 2D
  numeric array in the file.
- `backend/routers/ecg_router.py`: `ALLOWED_FORMATS` now includes `"mat"`.
- `frontend/src/pages/PatientDetail.jsx`: upload format dropdown now has a
  **MAT** option.

## 2. Complete Admin Panel (closes gap #2)
- New `backend/routers/admin_router.py`:
  - `GET /admin/users` — list all users
  - `DELETE /admin/users/{id}` — delete a user (blocks self-delete and
    deleting the last remaining admin)
  - `GET /admin/prediction-logs` — every prediction across all patients, with
    patient/doctor context
  - `GET /admin/usage-stats` — total users/patients/predictions/records,
    average confidence, breakdowns by role/class/risk/file-format, and a
    14-day prediction trend
  - User creation already existed at `POST /auth/users`; it's now reachable
    from the UI too.
- New `frontend/src/pages/Admin.jsx` — three tabs (Users, Prediction Logs,
  Usage Statistics) with Plotly charts for the stats tab, reusing existing
  visual language (RiskBadge, card styling, ink/teal palette).
- New `frontend/src/components/AdminRoute.jsx` — redirects non-admins away
  from `/admin`.
- `AppShell.jsx` — "Admin" nav item now shows up only for `role === "admin"`.

## 3. PDF report heatmap (closes gap #3)
- `backend/routers/ecg_router.py` now saves a companion `.saliency.npz` file
  (raw signal + full per-lead-over-time saliency map) alongside every
  upload — previously only 12 scalar per-lead numbers were persisted, which
  isn't enough to draw a real heatmap.
- `backend/models_db.py`: `ECGRecord` gained a `saliency_path` column
  pointing at that file.
- `backend/reports.py`: new `_build_saliency_heatmap_png()` renders a
  matplotlib leads×time heatmap image, embedded into the PDF under a new
  "ECG Saliency Heatmap" section.
- `backend/requirements.txt`: added `matplotlib`.

## Bugs found and fixed along the way (not requested, but blocking)
While actually running the app end-to-end to verify these changes, three
pre-existing bugs surfaced that would have broken the app for any real user:

1. **Every ECG upload and every patient-history call was broken.**
   `ECGRecordOut.model_validate(record)` tried to validate the raw SQLAlchemy
   `prediction` relationship directly against `PredictionOut`, which needs
   derived fields (`probs`, `predicted_classes`, etc.) that don't exist on the
   ORM object — this raised a `ValidationError` on every call in
   `ecg_router.py` and `patients_router.py`. Fixed by building the response
   dict directly from ORM fields instead of routing it through pydantic
   validation.
2. **Every WFDB upload failed with `FileNotFoundError`.** WFDB `.hea` files
   store the record name and `.dat` filename as literal text written at
   export time (e.g. `rec1.dat`). The app saves uploads under a new
   UUID-based name for collision-safety, but never updated those internal
   references, so `wfdb.rdrecord()` always went looking for the *original*
   filename next to the renamed header. Fixed with
   `_rewrite_wfdb_header_filenames()` in `ecg_router.py`.
3. **`passlib`/`bcrypt` version mismatch broke login/seeding entirely** —
   `passlib==1.7.4`'s bcrypt backend detection raises `ValueError` on
   `bcrypt>=4.1`. Pinned `bcrypt==4.0.1` in `requirements.txt`.

All three were verified fixed by actually running the FastAPI app (via
`TestClient`) through login, patient creation, CSV/NPY/MAT/WFDB upload,
history retrieval, all new admin endpoints, and PDF generation — not just
read from the source.

## What's still not covered
- No formal `alembic` migration for the new `ECGRecord.saliency_path`
  column — if you have an existing `patients.db` from before this change,
  delete it (or the whole `backend/database/` folder) and re-run
  `python seed.py` to pick up the new schema. All data in it is demo data
  anyway per the seed script.
- Admin "usage statistics" reads the whole `predictions`/`users`/`records`
  tables into memory to build the breakdowns — fine at demo/small-hospital
  scale, would want real SQL aggregation (`GROUP BY`) if this ever needs to
  scale to a large deployment.
