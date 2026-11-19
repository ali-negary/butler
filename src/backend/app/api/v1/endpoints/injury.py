from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.domain_models import InjuryLog as M
from app.schemas.domain_schemas import InjuryLogCreate, InjuryLogRead, InjuryLogUpdate
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=InjuryLogRead, status_code=201)
def create(obj: InjuryLogCreate, db: Session = Depends(get_db)):
    o = M.model_validate(obj)
    db.add(o); db.commit(); db.refresh(o)
    return o

@router.get("/{lid}", response_model=InjuryLogRead)
def read(lid: int, db: Session = Depends(get_db)):
    o = db.get(M, lid)
    if not o: raise HTTPException(404, "Not found")
    return o

@router.put("/{lid}", response_model=InjuryLogRead)
def update(lid: int, obj: InjuryLogUpdate, db: Session = Depends(get_db)):
    o = db.get(M, lid)
    if not o: raise HTTPException(404, "Not found")
    for k, v in obj.model_dump(exclude_unset=True).items(): setattr(o, k, v)
    db.add(o); db.commit(); db.refresh(o)
    return o

@router.get("/", response_model=list[InjuryLogRead])
def list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list(db.exec(select(M).offset(skip).limit(limit)).all())

@router.delete("/{lid}")
def delete(lid: int, db: Session = Depends(get_db)):
    o = db.get(M, lid)
    if not o: raise HTTPException(404, "Not found")
    db.delete(o); db.commit()
    return {"ok": True}
