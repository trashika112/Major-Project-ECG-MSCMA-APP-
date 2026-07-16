from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel


# ---- Auth ----
class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    full_name: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: str = "doctor"


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ---- Patients ----
class PatientCreate(BaseModel):
    patient_code: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    symptoms: Optional[str] = ""
    doctor_name: Optional[str] = ""


class PatientOut(PatientCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Predictions ----
class PredictionOut(BaseModel):
    id: int
    ecg_record_id: int
    probs: Dict[str, float]
    predicted_classes: List[str]
    thresholds: Dict[str, float]
    top_class: str
    top_confidence: float
    risk_level: str
    model_version: str
    saliency: Dict[str, float]
    created_at: datetime

    class Config:
        from_attributes = True


class ECGRecordOut(BaseModel):
    id: int
    patient_id: int
    original_filename: str
    file_format: str
    sampling_rate: int
    uploaded_at: datetime
    prediction: Optional[PredictionOut] = None

    # Only populated by the /ecg/upload response (right after a fresh
    # prediction) so the ECG viewer can draw the live signal + saliency
    # overlay. NOT persisted, and always None on /patients/{code}/history
    # (history rows re-use this same schema but never set these fields).
    raw_signal: Optional[List[List[float]]] = None
    saliency_timeseries: Optional[List[List[float]]] = None
    classes: Optional[List[str]] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    todays_patients: int
    predictions_today: int
    high_risk_cases: int
    normal_ecg: int


# ---- Admin ----
class PredictionLogOut(BaseModel):
    prediction_id: int
    ecg_record_id: int
    patient_code: str
    patient_name: str
    doctor_name: Optional[str] = ""
    top_class: str
    top_confidence: float
    risk_level: str
    model_version: str
    file_format: str
    created_at: datetime


class ClassCount(BaseModel):
    label: str
    count: int


class DailyCount(BaseModel):
    date: str
    count: int


class UsageStats(BaseModel):
    total_users: int
    total_patients: int
    total_predictions: int
    total_ecg_records: int
    avg_confidence: float
    users_by_role: List[ClassCount]
    predictions_by_class: List[ClassCount]
    predictions_by_risk: List[ClassCount]
    predictions_by_format: List[ClassCount]
    predictions_last_14_days: List[DailyCount]
