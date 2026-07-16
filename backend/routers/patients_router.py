from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
import models_db as m
import schemas as s
from auth import get_current_user

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=s.PatientOut)
def create_patient(payload: s.PatientCreate, db: Session = Depends(get_db),
                    _user: m.User = Depends(get_current_user)):
    if db.query(m.Patient).filter(m.Patient.patient_code == payload.patient_code).first():
        raise HTTPException(status_code=400, detail="A patient with this Patient ID already exists.")
    patient = m.Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=List[s.PatientOut])
def list_patients(q: str = "", db: Session = Depends(get_db),
                   _user: m.User = Depends(get_current_user)):
    query = db.query(m.Patient)
    if q:
        like = f"%{q}%"
        query = query.filter((m.Patient.name.ilike(like)) | (m.Patient.patient_code.ilike(like)))
    return query.order_by(m.Patient.created_at.desc()).all()


@router.get("/{patient_code}", response_model=s.PatientOut)
def get_patient(patient_code: str, db: Session = Depends(get_db),
                 _user: m.User = Depends(get_current_user)):
    patient = db.query(m.Patient).filter(m.Patient.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@router.get("/{patient_code}/history", response_model=List[s.ECGRecordOut])
def patient_history(patient_code: str, db: Session = Depends(get_db),
                     _user: m.User = Depends(get_current_user)):
    patient = db.query(m.Patient).filter(m.Patient.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    records = sorted(patient.ecg_records, key=lambda r: r.uploaded_at, reverse=True)
    return [_serialize_record(r) for r in records]


def _serialize_record(r: m.ECGRecord) -> dict:
    out = {
        "id": r.id,
        "patient_id": r.patient_id,
        "original_filename": r.original_filename,
        "file_format": r.file_format,
        "sampling_rate": r.sampling_rate,
        "uploaded_at": r.uploaded_at,
        "prediction": None,
    }
    if r.prediction:
        import json
        p = r.prediction
        out["prediction"] = {
            "id": p.id, "ecg_record_id": p.ecg_record_id,
            "probs": json.loads(p.probs_json),
            "predicted_classes": json.loads(p.predicted_classes_json),
            "thresholds": json.loads(p.thresholds_json or "{}"),
            "top_class": p.top_class, "top_confidence": p.top_confidence,
            "risk_level": p.risk_level, "model_version": p.model_version,
            "saliency": json.loads(p.saliency_json or "{}"),
            "created_at": p.created_at,
        }
    return out


dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/stats", response_model=s.DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), _user: m.User = Depends(get_current_user)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    todays_patients = db.query(m.Patient).filter(m.Patient.created_at >= today_start).count()
    predictions_today = db.query(m.Prediction).filter(m.Prediction.created_at >= today_start).count()
    high_risk_cases = db.query(m.Prediction).filter(
        m.Prediction.created_at >= today_start, m.Prediction.risk_level == "HIGH").count()
    normal_ecg = db.query(m.Prediction).filter(
        m.Prediction.created_at >= today_start, m.Prediction.top_class == "NORM").count()

    return s.DashboardStats(
        todays_patients=todays_patients,
        predictions_today=predictions_today,
        high_risk_cases=high_risk_cases,
        normal_ecg=normal_ecg,
    )
