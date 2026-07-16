import os
import json
import shutil
import uuid
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
import models_db as m
import schemas as s
from auth import get_current_user
from config import UPLOAD_DIR, CLASSES
from predict import ModelService
from preprocessing import load_ecg_file, ECGFormatError, ECGValidityError
from reports import build_report_pdf

router = APIRouter(prefix="/ecg", tags=["ecg"])

ALLOWED_FORMATS = {"csv", "npy", "mat", "wfdb"}


def _rewrite_wfdb_header_filenames(hea_path: str, new_stem: str) -> None:
    """WFDB .hea files store the record name (line 1, first token) and the
    .dat filename (every signal line, first token) as literal text written at
    export time — e.g. 'rec1.dat'. We save uploads under a new uid-based name
    to avoid collisions, so without this rewrite, wfdb.rdrecord() would still
    go looking for the *original* filename (e.g. 'rec1.dat') next to our
    renamed header and fail with FileNotFoundError. This patches every line's
    filename/record-name token to match the file we actually saved."""
    with open(hea_path, "r") as f:
        lines = f.read().splitlines()
    if not lines:
        return

    fixed_lines = []
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith("#"):
            fixed_lines.append(line)
            continue
        parts = line.split(" ")
        if i == 0:
            # header line: "<record_name> <n_sig> <fs> <n_samples> ..."
            parts[0] = new_stem
        else:
            # signal line: "<filename> <format> ..." -- filename keeps its extension
            old_token = parts[0]
            ext = os.path.splitext(old_token)[1] or ".dat"
            parts[0] = new_stem + ext
        fixed_lines.append(" ".join(parts))

    with open(hea_path, "w") as f:
        f.write("\n".join(fixed_lines) + "\n")


@router.post("/upload", response_model=s.ECGRecordOut)
async def upload_and_predict(
    patient_code: str = Form(...),
    file_format: str = Form(...),
    sampling_rate: int = Form(100),
    file: UploadFile = File(...),
    hea_file: UploadFile = File(None),   # only needed when file_format == "wfdb"
    db: Session = Depends(get_db),
    _user: m.User = Depends(get_current_user),
):
    file_format = file_format.lower()
    if file_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"file_format must be one of {sorted(ALLOWED_FORMATS)}.")

    patient = db.query(m.Patient).filter(m.Patient.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found. Register the patient first.")

    # Save the uploaded file(s) to disk under a unique name.
    uid = uuid.uuid4().hex[:12]
    ext = {"csv": ".csv", "npy": ".npy", "mat": ".mat", "wfdb": ".dat"}[file_format]
    dest_path = os.path.join(UPLOAD_DIR, f"{patient_code}_{uid}{ext}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if file_format == "wfdb":
        if hea_file is None:
            raise HTTPException(status_code=400, detail="WFDB format needs both a .dat and a .hea file.")
        hea_dest = dest_path[:-4] + ".hea"
        with open(hea_dest, "wb") as f:
            shutil.copyfileobj(hea_file.file, f)
        _rewrite_wfdb_header_filenames(hea_dest, new_stem=os.path.basename(dest_path)[:-4])

    try:
        raw = load_ecg_file(dest_path, file_format, sampling_rate)
    except ECGFormatError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ECGValidityError as e:
        raise HTTPException(status_code=422, detail=f"Not a valid ECG signal: {e}")

    service = ModelService.instance()
    result = service.predict(raw)

    # Persist the raw signal + full per-lead-over-time saliency map so the PDF
    # report (generated later, possibly in a different request) can render a
    # real heatmap image instead of just the 12 scalar per-lead numbers.
    saliency_npz_path = dest_path + ".saliency.npz"
    np.savez_compressed(
        saliency_npz_path,
        raw=raw.astype(np.float32),                                       # (T, leads)
        saliency=np.asarray(result["saliency_timeseries"], dtype=np.float32),  # (leads, T)
    )

    record = m.ECGRecord(
        patient_id=patient.id,
        file_path=dest_path,
        original_filename=file.filename,
        file_format=file_format,
        sampling_rate=sampling_rate,
        saliency_path=saliency_npz_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    prediction = m.Prediction(
        ecg_record_id=record.id,
        probs_json=json.dumps(result["probs"]),
        predicted_classes_json=json.dumps(result["predicted_classes"]),
        thresholds_json=json.dumps(result["thresholds"]),
        top_class=result["top_class"],
        top_confidence=result["top_confidence"],
        risk_level=result["risk_level"],
        saliency_json=json.dumps(result["saliency"]),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    db.refresh(record)

    out = {
        "id": record.id,
        "patient_id": record.patient_id,
        "original_filename": record.original_filename,
        "file_format": record.file_format,
        "sampling_rate": record.sampling_rate,
        "uploaded_at": record.uploaded_at,
        "prediction": None,
    }
    out["prediction"] = {
        "id": prediction.id, "ecg_record_id": prediction.ecg_record_id,
        "probs": result["probs"], "predicted_classes": result["predicted_classes"],
        "thresholds": result["thresholds"], "top_class": result["top_class"],
        "top_confidence": result["top_confidence"], "risk_level": result["risk_level"],
        "model_version": prediction.model_version, "saliency": result["saliency"],
        "created_at": prediction.created_at,
    }
    # Full time-series saliency + raw signal are only returned live (not persisted)
    # so the ECG viewer can draw the heatmap overlay right after upload.
    out["raw_signal"] = raw.tolist()
    out["saliency_timeseries"] = result["saliency_timeseries"]
    out["classes"] = CLASSES
    return out


@router.get("/record/{record_id}/report")
def download_report(record_id: int, db: Session = Depends(get_db),
                     _user: m.User = Depends(get_current_user)):
    record = db.query(m.ECGRecord).filter(m.ECGRecord.id == record_id).first()
    if not record or not record.prediction:
        raise HTTPException(status_code=404, detail="Record or prediction not found.")
    path = build_report_pdf(record.patient, record, record.prediction, saliency_path=record.saliency_path)
    return FileResponse(path, media_type="application/pdf",
                         filename=os.path.basename(path))
