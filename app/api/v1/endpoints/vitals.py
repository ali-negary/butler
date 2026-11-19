from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from datetime import date as _date
from app.models.domain_models import DailyVitals as M
from app.schemas.domain_schemas import DailyVitalsCreate, DailyVitalsRead, DailyVitalsUpdate
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=DailyVitalsRead, status_code=201)
def create_vital(obj: DailyVitalsCreate, db: Session = Depends(get_db)):
    if db.get(M, obj.date):
        raise HTTPException(status_code=400, detail="Vitals for this date already exist")
    m = M.model_validate(obj)
    db.add(m); db.commit(); db.refresh(m)
    return DailyVitalsRead.model_validate(m)

@router.get("/{date}", response_model=DailyVitalsRead)
def read_vital(date: str, db: Session = Depends(get_db)):
    m = db.get(M, _date.fromisoformat(date))
    if not m: raise HTTPException(status_code=404, detail="Not found")
    return DailyVitalsRead.model_validate(m)

@router.put("/{date}", response_model=DailyVitalsRead)
def update_vital(date: str, obj: DailyVitalsUpdate, db: Session = Depends(get_db)):
    m = db.get(M, _date.fromisoformat(date))
    if not m: raise HTTPException(status_code=404, detail="Not found")
    d = obj.model_dump(exclude_unset=True)
    for k, v in d.items(): setattr(m, k, v)
    db.add(m); db.commit(); db.refresh(m)
    return DailyVitalsRead.model_validate(m)

@router.get("/", response_model=list[DailyVitalsRead])
def list_vitals(skip: int = 0, limit: int = 100, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    stmt = select(M).offset(skip).limit(limit)
    if start_date: stmt = stmt.where(M.date >= _date.fromisoformat(start_date))
    if end_date: stmt = stmt.where(M.date <= _date.fromisoformat(end_date))
    return [DailyVitalsRead.model_validate(m) for m in db.exec(stmt).all()]

@router.delete("/{date}")
def delete_vital(date: str, db: Session = Depends(get_db)):
    m = db.get(M, _date.fromisoformat(date))
    if not m: raise HTTPException(status_code=404, detail="Not found")
    db.delete(m); db.commit()
    return {"ok": True}
