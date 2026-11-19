from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timezone
from app.models.domain_models import StrengthSession as SM, StrengthSet as SS
from app.schemas.domain_schemas import StrengthSessionCreate, StrengthSessionRead, StrengthSessionUpdate, StrengthSetCreate, StrengthSetRead, StrengthSetUpdate
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=StrengthSessionRead, status_code=201)
def create(obj: StrengthSessionCreate, db: Session = Depends(get_db)):
    s = SM.model_validate(obj.model_dump(exclude={"sets"}))
    s.created_at = datetime.now(timezone.utc)
    s.updated_at = s.created_at
    db.add(s); db.flush()
    for sd in (obj.sets or []):
        db.add(SS.model_validate({**sd.model_dump(), "session_id": s.id}))
    db.commit(); db.refresh(s)
    return s

@router.get("/{sid}", response_model=StrengthSessionRead)
def read(sid: int, db: Session = Depends(get_db)):
    s = db.get(SM, sid)
    if not s: raise HTTPException(404, "Not found")
    return s

@router.put("/{sid}", response_model=StrengthSessionRead)
def update(sid: int, obj: StrengthSessionUpdate, db: Session = Depends(get_db)):
    s = db.get(SM, sid)
    if not s: raise HTTPException(404, "Not found")
    for k, v in obj.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    s.updated_at = datetime.now(timezone.utc)
    db.add(s); db.commit(); db.refresh(s)
    return s

@router.get("/", response_model=list[StrengthSessionRead])
def list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.exec(select(SM).offset(skip).limit(limit)).all()
    return [StrengthSessionRead.model_validate(s) for s in items]

@router.delete("/{sid}")
def delete(sid: int, db: Session = Depends(get_db)):
    s = db.get(SM, sid)
    if not s: raise HTTPException(404, "Not found")
    db.delete(s); db.commit()
    return {"ok": True}


@router.post("/{sid}/sets/", response_model=StrengthSetRead, status_code=201)
def create_set(sid: int, obj: StrengthSetCreate, db: Session = Depends(get_db)):
    if not db.get(SM, sid): raise HTTPException(404, "Session not found")
    o = SS.model_validate({**obj.model_dump(), "session_id": sid})
    db.add(o); db.commit(); db.refresh(o)
    return o

@router.put("/sets/{sid}", response_model=StrengthSetRead)
def update_set(sid: int, obj: StrengthSetUpdate, db: Session = Depends(get_db)):
    s = db.get(SS, sid)
    if not s: raise HTTPException(404, "Not found")
    for k, v in obj.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    db.add(s); db.commit(); db.refresh(s)
    return s

@router.delete("/sets/{sid}")
def delete_set(sid: int, db: Session = Depends(get_db)):
    s = db.get(SS, sid)
    if not s: raise HTTPException(404, "Not found")
    db.delete(s); db.commit()
    return {"ok": True}
