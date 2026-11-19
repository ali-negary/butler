from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.domain_models import LifestyleSession as M
from app.schemas.domain_schemas import LifestyleSessionCreate, LifestyleSessionRead, LifestyleSessionUpdate
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=LifestyleSessionRead, status_code=201)
def create(obj: LifestyleSessionCreate, db: Session = Depends(get_db)):
    o = M.model_validate(obj)
    db.add(o); db.commit(); db.refresh(o)
    return o

@router.get("/{sid}", response_model=LifestyleSessionRead)
def read(sid: int, db: Session = Depends(get_db)):
    o = db.get(M, sid)
    if not o: raise HTTPException(404, "Not found")
    return o

@router.put("/{sid}", response_model=LifestyleSessionRead)
def update(sid: int, obj: LifestyleSessionUpdate, db: Session = Depends(get_db)):
    o = db.get(M, sid)
    if not o: raise HTTPException(404, "Not found")
    for k, v in obj.model_dump(exclude_unset=True).items(): setattr(o, k, v)
    db.add(o); db.commit(); db.refresh(o)
    return o

@router.get("/", response_model=list[LifestyleSessionRead])
def list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list(db.exec(select(M).offset(skip).limit(limit)).all())

@router.delete("/{sid}")
def delete(sid: int, db: Session = Depends(get_db)):
    o = db.get(M, sid)
    if not o: raise HTTPException(404, "Not found")
    db.delete(o); db.commit()
    return {"ok": True}
