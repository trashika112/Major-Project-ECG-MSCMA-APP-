"""Run once: `python seed.py` — creates the database tables and a few default
logins so you can try the frontend immediately. CHANGE THESE PASSWORDS before
using this anywhere real."""
from database import Base, engine, SessionLocal
import models_db as m
from auth import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "full_name": "System Admin", "role": "admin"},
    {"username": "doctor", "password": "doctor123", "full_name": "Dr. A. Sharma", "role": "doctor"},
    {"username": "cardio", "password": "cardio123", "full_name": "Dr. R. Iyer", "role": "cardiologist"},
    {"username": "nurse", "password": "nurse123", "full_name": "Nurse J. Fernandes", "role": "nurse"},
]

for u in DEFAULT_USERS:
    exists = db.query(m.User).filter(m.User.username == u["username"]).first()
    if not exists:
        db.add(m.User(username=u["username"], hashed_password=hash_password(u["password"]),
                      full_name=u["full_name"], role=u["role"]))
        print(f"Created user '{u['username']}' / '{u['password']}' (role={u['role']})")
    else:
        print(f"User '{u['username']}' already exists, skipping.")

db.commit()
db.close()
print("\nDone. Start the API with: uvicorn app:app --reload --port 8000")
