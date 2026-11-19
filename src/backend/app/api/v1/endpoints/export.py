from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session
from typing import Optional
from app.api.dependencies import get_db

router = APIRouter()


@router.get("/csv")
def export_csv(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Redirect to /api/v1/ingest/csv for CSV export."""
    raise HTTPException(status_code=307, detail="Use /api/v1/ingest/csv instead")


@router.get("/json")
def export_json(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Redirect to /api/v1/ingest/json for JSON export."""
    raise HTTPException(status_code=307, detail="Use /api/v1/ingest/json instead")
