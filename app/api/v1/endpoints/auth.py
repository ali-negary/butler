from fastapi import APIRouter, Depends, HTTPException, Form
from sqlmodel import Session, select
from app.models.domain_models import User as UserModel
from app.schemas.domain_schemas import UserCreate, UserRead, Token
from app.api.dependencies import get_db, authenticate_user, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.exec(select(UserModel).where(UserModel.email == user_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return authenticate_user(db, user_data.email, user_data.password, register=True, full_name=user_data.full_name)

@router.post("/login", response_model=Token)
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
