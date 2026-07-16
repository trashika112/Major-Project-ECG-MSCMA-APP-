from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers.auth_router import router as auth_router
from routers.patients_router import router as patients_router, dashboard_router
from routers.ecg_router import router as ecg_router
from routers.admin_router import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ECG Clinical Decision Support System API",
    description="Backend for the MSCMA-Net ECG prediction demo app.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(dashboard_router)
app.include_router(ecg_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "ECG Clinical Decision Support System API"}


@app.get("/health")
def health():
    from predict import ModelService
    service = ModelService.instance()
    return {"model_loaded": service.loaded, "device": str(service.device)}
