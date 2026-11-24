import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from hashlib import sha256
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.config import get_settings
from app.core.db import get_sync_db
from app.models.domain_models import User as UserModel

settings = get_settings()

# Re-export as get_db so all existing endpoint imports work
get_db = get_sync_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return _hash_password(plain_password) == hashed_password


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def authenticate_user(db: Session, email: str, password: str, register: bool = False, full_name: Optional[str] = None) -> Optional[UserModel]:
    user = db.exec(select(UserModel).where(UserModel.email == email)).first()
    if user:
        if not _verify_password(password, user.hashed_password):
            return None
        return user
    if register:
        new_user = UserModel(
            email=email,
            full_name=full_name,
            hashed_password=_hash_password(password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    return None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except JWTError:
        raise credentials_exception
    user = db.get(UserModel, user_id)
    if user is None:
        raise credentials_exception
    return user


def verify_token(token: str = Depends(oauth2_scheme)):
    return get_current_user(token)
