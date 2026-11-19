from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.db import get_db
from app.models.domain_models import User as UserModel

SECRET_KEY = "project-butler-dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str, register: bool = False, full_name: Optional[str] = None) -> Optional[UserModel]:
    user = db.exec(select(UserModel).where(UserModel.email == email)).first()
    if user:
        if not verify_password(password, user.hashed_password):
            return None
        return user
    if register:
        new_user = UserModel(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
