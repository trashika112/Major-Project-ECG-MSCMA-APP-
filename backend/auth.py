from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
import models_db as m

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> m.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials — please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(m.User).filter(m.User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*allowed_roles: str):
    def dependency(user: m.User = Depends(get_current_user)) -> m.User:
        if user.role not in allowed_roles and user.role != "admin":
            raise HTTPException(status_code=403, detail="You don't have permission to do this.")
        return user
    return dependency
