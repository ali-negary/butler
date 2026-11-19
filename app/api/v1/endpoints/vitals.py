from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date as date_type
from app.models.domain_models import DailyVitals as DailyVitalsModel, NutritionLog as NutritionLogModel, StrengthSession as StrengthSessionModel, StrengthSet as StrengthSetModel, CardioSession as CardioSessionModel, LifestyleSession as LifestyleSessionModel, InjuryLog as InjuryLogModel
from app.schemas.domain_schemas import DailyVitalsCreate, DailyVitalsRead, DailyVitalsUpdate, StrengthSessionCreate, StrengthSessionRead, StrengthSessionUpdate, StrengthSetCreate, StrengthSetRead, StrengthSetUpdate, CardioSessionCreate, CardioSessionRead, CardioSessionUpdate, LifestyleSessionCreate, LifestyleSessionRead, LifestyleSessionUpdate, NutritionLogCreate, NutritionLogRead, NutritionLogUpdate, InjuryLogCreate, InjuryLogRead, InjuryLogUpdate
from app.api.dependencies import get_db
from app.crud.base import CRUDByDate

router = APIRouter()

# ── Vitals ────────────────────────────────────────────────────────────────

@router.post("/", response_model=DailyVitalsRead, status_code=201)
def create_vital(vital: DailyVitalsCreate, db: Session = Depends(get_db)):
    db_vital = db.get(DailyVitalsModel, vital.date)
    if db_vital:
        raise HTTPException(status_code=400, detail="Vitals for this date already exist")
    return CRUDByDate(DailyVitalsModel).create(db, obj_in=vital)

@router.get("/{date}", response_model=DailyVitalsRead)
def read_vital(date: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    vital = CRUDByDate(DailyVitalsModel).get(db, date_type.fromisoformat(date))
    if not vital:
        raise HTTPException(status_code=404, detail="Vital not found")
    return vital

@router.put("/{date}", response_model=DailyVitalsRead)
def update_vital(date: str, vital: DailyVitalsUpdate, db: Session = Depends(get_db)):
    from datetime import date as date_type
    db_vital = CRUDByDate(DailyVitalsModel).get(db, date_type.fromisoformat(date))
    if not db_vital:
        raise HTTPException(status_code=404, detail="Vital not found")
    return CRUDByDate(DailyVitalsModel).update(db, date_value=date_type.fromisoformat(date), obj_in=vital)

@router.get("/", response_model=List[DailyVitalsRead])
def read_vitals(skip: int = 0, limit: int = 100, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    from datetime import date as date_type
    sd = date_type.fromisoformat(start_date) if start_date else None
    ed = date_type.fromisoformat(end_date) if end_date else None
    return CRUDByDate(DailyVitalsModel).get_multi(db, skip=skip, limit=limit, start_date=sd, end_date=ed)

@router.delete("/{date}")
def delete_vital(date: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    deleted = CRUDByDate(DailyVitalsModel).delete(db, date_value=date_type.fromisoformat(date))
    if not deleted:
        raise HTTPException(status_code=404, detail="Vital not found")
    return {"ok": True}

# ── Strength Sessions ────────────────────────────────────────────────────

@router.post("/strength/", response_model=StrengthSessionRead, status_code=201)
def create_strength_session(session: StrengthSessionCreate, db: Session = Depends(get_db)):
    db_session = StrengthSessionModel.model_validate(session.model_dump(exclude={"sets"}))
    db.add(db_session)
    db.flush()
    for set_data in (session.sets or []):
        strength_set = StrengthSetModel.model_validate({**set_data.model_dump(), "session_id": db_session.id})
        db.add(strength_set)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/strength/{session_id}", response_model=StrengthSessionRead)
def read_strength_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.get(StrengthSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.put("/strength/{session_id}", response_model=StrengthSessionRead)
def update_strength_session(session_id: int, session: StrengthSessionUpdate, db: Session = Depends(get_db)):
    db_session = db.get(StrengthSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_data = session.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/strength/", response_model=List[StrengthSessionRead])
def read_strength_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list(db.exec(select(StrengthSessionModel).offset(skip).limit(limit)).all())

@router.delete("/strength/{session_id}")
def delete_strength_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.get(StrengthSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"ok": True}

# ── Strength Sets ────────────────────────────────────────────────────────

@router.post("/strength/{session_id}/sets/", response_model=StrengthSetRead, status_code=201)
def create_strength_set(session_id: int, s: StrengthSetCreate, db: Session = Depends(get_db)):
    if not db.get(StrengthSessionModel, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    set_obj = StrengthSetModel.model_validate({**s.model_dump(), "session_id": session_id})
    db.add(set_obj)
    db.commit()
    db.refresh(set_obj)
    return set_obj

@router.put("/strength/sets/{set_id}", response_model=StrengthSetRead)
def update_strength_set(set_id: int, s: StrengthSetUpdate, db: Session = Depends(get_db)):
    db_set = db.get(StrengthSetModel, set_id)
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")
    update_data = s.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_set, field, value)
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set

@router.delete("/strength/sets/{set_id}")
def delete_strength_set(set_id: int, db: Session = Depends(get_db)):
    db_set = db.get(StrengthSetModel, set_id)
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found")
    db.delete(db_set)
    db.commit()
    return {"ok": True}

# ── Cardio ──────────────────────────────────────────────────────────────

@router.post("/cardio/", response_model=CardioSessionRead, status_code=201)
def create_cardio_session(session: CardioSessionCreate, db: Session = Depends(get_db)):
    db_session = CardioSessionModel.model_validate(session)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/cardio/{session_id}", response_model=CardioSessionRead)
def read_cardio_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.get(CardioSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.put("/cardio/{session_id}", response_model=CardioSessionRead)
def update_cardio_session(session_id: int, session: CardioSessionUpdate, db: Session = Depends(get_db)):
    db_session = db.get(CardioSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_data = session.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/cardio/", response_model=List[CardioSessionRead])
def read_cardio_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list(db.exec(select(CardioSessionModel).offset(skip).limit(limit)).all())

@router.delete("/cardio/{session_id}")
def delete_cardio_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.get(CardioSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"ok": True}

# ── Lifestyle ───────────────────────────────────────────────────────────

@router.post("/lifestyle/", response_model=LifestyleSessionRead, status_code=201)
def create_lifestyle_session(session: LifestyleSessionCreate, db: Session = Depends(get_db)):
    db_session = LifestyleSessionModel.model_validate(session)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/lifestyle/{session_id}", response_model=LifestyleSessionRead)
def read_lifestyle_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.get(LifestyleSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.put("/lifestyle/{session_id}", response_model=LifestyleSessionRead)
def update_lifestyle_session(session_id: int, session: LifestyleSessionUpdate, db: Session = Depends(get_db)):
    db_session = db.get(LifestyleSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_data = session.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/lifestyle/", response_model=List[LifestyleSessionRead])
def read_lifestyle_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list(db.exec(select(LifestyleSessionModel).offset(skip).limit(limit)).all())

@router.delete("/lifestyle/{session_id}")
def delete_lifestyle_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.get(LifestyleSessionModel, session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"ok": True}

# ── Nutrition ───────────────────────────────────────────────────────────

@router.post("/nutrition/", response_model=NutritionLogRead, status_code=201)
def create_nutrition_log(log: NutritionLogCreate, db: Session = Depends(get_db)):
    return CRUDByDate(NutritionLogModel).create(db, obj_in=log)

@router.get("/nutrition/{date}", response_model=NutritionLogRead)
def read_nutrition_log(date: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    log = CRUDByDate(NutritionLogModel).get(db, date_type.fromisoformat(date))
    if not log:
        raise HTTPException(status_code=404, detail="Nutrition log not found")
    return log

@router.put("/nutrition/{date}", response_model=NutritionLogRead)
def update_nutrition_log(date: str, log: NutritionLogUpdate, db: Session = Depends(get_db)):
    from datetime import date as date_type
    db_log = CRUDByDate(NutritionLogModel).get(db, date_type.fromisoformat(date))
    if not db_log:
        raise HTTPException(status_code=404, detail="Nutrition log not found")
    return CRUDByDate(NutritionLogModel).update(db, date_value=date_type.fromisoformat(date), obj_in=log)

@router.get("/nutrition/", response_model=List[NutritionLogRead])
def read_nutrition_logs(skip: int = 0, limit: int = 100, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    from datetime import date as date_type
    sd = date_type.fromisoformat(start_date) if start_date else None
    ed = date_type.fromisoformat(end_date) if end_date else None
    return CRUDByDate(NutritionLogModel).get_multi(db, skip=skip, limit=limit, start_date=sd, end_date=ed)

@router.delete("/nutrition/{date}")
def delete_nutrition_log(date: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    deleted = CRUDByDate(NutritionLogModel).delete(db, date_value=date_type.fromisoformat(date))
    if not deleted:
        raise HTTPException(status_code=404, detail="Nutrition log not found")
    return {"ok": True}

# ── Injury ──────────────────────────────────────────────────────────────

@router.post("/injury/", response_model=InjuryLogRead, status_code=201)
def create_injury_log(log: InjuryLogCreate, db: Session = Depends(get_db)):
    db_log = InjuryLogModel.model_validate(log)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("/injury/{log_id}", response_model=InjuryLogRead)
def read_injury_log(log_id: int, db: Session = Depends(get_db)):
    db_log = db.get(InjuryLogModel, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Injury log not found")
    return db_log

@router.put("/injury/{log_id}", response_model=InjuryLogRead)
def update_injury_log(log_id: int, log: InjuryLogUpdate, db: Session = Depends(get_db)):
    db_log = db.get(InjuryLogModel, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Injury log not found")
    update_data = log.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_log, field, value)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("/injury/", response_model=List[InjuryLogRead])
def read_injury_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list(db.exec(select(InjuryLogModel).offset(skip).limit(limit)).all())

@router.delete("/injury/{log_id}")
def delete_injury_log(log_id: int, db: Session = Depends(get_db)):
    db_log = db.get(InjuryLogModel, log_id)
    if not db_log:
        raise HTTPException(status_code=404, detail="Injury log not found")
    db.delete(db_log)
    db.commit()
    return {"ok": True}
