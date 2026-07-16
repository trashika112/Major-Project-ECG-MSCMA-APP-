from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
import models_db as m
import schemas as s
from auth import verify_password, create_access_token, hash_password, get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=s.Token)
def login(payload: s.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(m.User).filter(m.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been disabled.")
    if payload.role and payload.role != user.role:
        raise HTTPException(status_code=401, detail="Role does not match this account.")

    token = create_access_token({"sub": user.username, "role": user.role})
    return s.Token(access_token=token, username=user.username, role=user.role, full_name=user.full_name)


@router.get("/me", response_model=s.UserOut)
def me(user: m.User = Depends(get_current_user)):
    return user


@router.post("/users", response_model=s.UserOut)
def create_user(payload: s.UserCreate, db: Session = Depends(get_db),
                 _admin: m.User = Depends(require_role("admin"))):
    if db.query(m.User).filter(m.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists.")
    user = m.User(username=payload.username, hashed_password=hash_password(payload.password),
                  full_name=payload.full_name, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
