from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date as date_type
from app.models.domain_models import NutritionLog as M
from app.schemas.domain_schemas import NutritionLogCreate, NutritionLogRead, NutritionLogUpdate
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=NutritionLogRead, status_code=201)
def create(obj: NutritionLogCreate, db: Session = Depends(get_db)):
    m = M.model_validate(obj); m.date = obj.date
    db.add(m); db.commit(); db.refresh(m)
    return NutritionLogRead.model_validate(m)

@router.get("/{date}", response_model=NutritionLogRead)
def read(date: str, db: Session = Depends(get_db)):
    m = db.get(M, date_type.fromisoformat(date))
    if not m: raise HTTPException(404, "Not found")
    return NutritionLogRead.model_validate(m)

@router.put("/{date}", response_model=NutritionLogRead)
def update(date: str, obj: NutritionLogUpdate, db: Session = Depends(get_db)):
    m = db.get(M, date_type.fromisoformat(date))
    if not m: raise HTTPException(404, "Not found")
    for k, v in obj.model_dump(exclude_unset=True).items(): setattr(m, k, v)
    db.add(m); db.commit(); db.refresh(m)
    return NutritionLogRead.model_validate(m)

@router.get("/", response_model=list[NutritionLogRead])
def list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return [NutritionLogRead.model_validate(m) for m in db.exec(select(M).offset(skip).limit(limit)).all()]

@router.delete("/{date}")
def delete(date: str, db: Session = Depends(get_db)):
    m = db.get(M, date_type.fromisoformat(date))
    if not m: raise HTTPException(404, "Not found")
    db.delete(m); db.commit()
    return {"ok": True}
