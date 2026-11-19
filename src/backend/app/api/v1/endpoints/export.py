from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session
from typing import Optional
from app.api.dependencies import get_db

router = APIRouter()

@router.get("/csv")
def export_csv(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Data export pipeline not yet implemented.")

@router.get("/json")
def export_json(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Data export pipeline not yet implemented.")
