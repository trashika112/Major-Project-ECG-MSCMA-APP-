from datetime import datetime, timedelta
from collections import Counter
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
import models_db as m
import schemas as s
from auth import require_role

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@router.get("/users", response_model=List[s.UserOut])
def list_users(db: Session = Depends(get_db), _admin: m.User = Depends(require_role("admin"))):
    return db.query(m.User).order_by(m.User.created_at.desc()).all()


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db),
                 admin: m.User = Depends(require_role("admin"))):
    user = db.query(m.User).filter(m.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You can't delete your own account while logged in as it.")
    if user.role == "admin":
        remaining_admins = db.query(m.User).filter(m.User.role == "admin", m.User.id != user.id).count()
        if remaining_admins == 0:
            raise HTTPException(status_code=400, detail="Can't delete the last remaining admin account.")
    db.delete(user)
    db.commit()
    return {"status": "deleted", "user_id": user_id}


# ---------------------------------------------------------------------------
# Prediction logs
# ---------------------------------------------------------------------------
@router.get("/prediction-logs", response_model=List[s.PredictionLogOut])
def prediction_logs(limit: int = 200, db: Session = Depends(get_db),
                     _admin: m.User = Depends(require_role("admin"))):
    rows = (
        db.query(m.Prediction, m.ECGRecord, m.Patient)
        .join(m.ECGRecord, m.Prediction.ecg_record_id == m.ECGRecord.id)
        .join(m.Patient, m.ECGRecord.patient_id == m.Patient.id)
        .order_by(m.Prediction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        s.PredictionLogOut(
            prediction_id=pred.id,
            ecg_record_id=rec.id,
            patient_code=patient.patient_code,
            patient_name=patient.name,
            doctor_name=patient.doctor_name,
            top_class=pred.top_class,
            top_confidence=pred.top_confidence,
            risk_level=pred.risk_level,
            model_version=pred.model_version,
            file_format=rec.file_format,
            created_at=pred.created_at,
        )
        for pred, rec, patient in rows
    ]


# ---------------------------------------------------------------------------
# Usage statistics
# ---------------------------------------------------------------------------
@router.get("/usage-stats", response_model=s.UsageStats)
def usage_stats(db: Session = Depends(get_db), _admin: m.User = Depends(require_role("admin"))):
    users = db.query(m.User).all()
    predictions = db.query(m.Prediction).all()
    records = db.query(m.ECGRecord).all()
    patients_count = db.query(m.Patient).count()

    role_counts = Counter(u.role for u in users)
    class_counts = Counter(p.top_class for p in predictions)
    risk_counts = Counter(p.risk_level for p in predictions)
    format_counts = Counter(r.file_format for r in records)

    avg_conf = (sum(p.top_confidence for p in predictions) / len(predictions)) if predictions else 0.0

    # last 14 days, oldest -> newest, zero-filled for days with no predictions
    today = datetime.utcnow().date()
    day_buckets = {(today - timedelta(days=i)): 0 for i in range(13, -1, -1)}
    for p in predictions:
        d = p.created_at.date()
        if d in day_buckets:
            day_buckets[d] += 1

    return s.UsageStats(
        total_users=len(users),
        total_patients=patients_count,
        total_predictions=len(predictions),
        total_ecg_records=len(records),
        avg_confidence=float(avg_conf),
        users_by_role=[s.ClassCount(label=k, count=v) for k, v in sorted(role_counts.items())],
        predictions_by_class=[s.ClassCount(label=k, count=v) for k, v in sorted(class_counts.items())],
        predictions_by_risk=[s.ClassCount(label=k, count=v) for k, v in sorted(risk_counts.items())],
        predictions_by_format=[s.ClassCount(label=k, count=v) for k, v in sorted(format_counts.items())],
        predictions_last_14_days=[
            s.DailyCount(date=d.isoformat(), count=c) for d, c in day_buckets.items()
        ],
    )
