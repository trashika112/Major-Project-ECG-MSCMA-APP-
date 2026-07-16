from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="doctor")  # doctor | cardiologist | nurse | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, unique=True, index=True, nullable=False)  # human-facing Patient ID
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    blood_pressure = Column(String)
    heart_rate = Column(Integer)
    symptoms = Column(Text, default="")
    doctor_name = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    ecg_records = relationship("ECGRecord", back_populates="patient", cascade="all, delete-orphan")


class ECGRecord(Base):
    __tablename__ = "ecg_records"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String)
    file_format = Column(String)  # csv | npy | mat | wfdb
    sampling_rate = Column(Integer, default=100)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    # .npz on disk holding the raw (T, leads) signal + full (leads, T) saliency
    # map computed at upload time, so the PDF report can render a real
    # per-lead-over-time heatmap later (not just the 12 scalar summary values
    # in Prediction.saliency_json).
    saliency_path = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="ecg_records")
    prediction = relationship("Prediction", back_populates="ecg_record", uselist=False,
                               cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    ecg_record_id = Column(Integer, ForeignKey("ecg_records.id"), nullable=False)
    probs_json = Column(Text, nullable=False)      # {"NORM":0.01,"MI":0.96,...}
    predicted_classes_json = Column(Text, nullable=False)  # ["MI","STTC"]
    thresholds_json = Column(Text, default="{}")
    top_class = Column(String)
    top_confidence = Column(Float)
    risk_level = Column(String)  # HIGH | MODERATE | LOW
    model_version = Column(String, default="MSCMA-Net v1")
    saliency_json = Column(Text, default="{}")  # per-lead saliency summary for the heatmap view
    created_at = Column(DateTime, default=datetime.utcnow)

    ecg_record = relationship("ECGRecord", back_populates="prediction")
