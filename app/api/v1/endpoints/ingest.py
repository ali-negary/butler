from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlmodel import Session
from typing import List, Optional
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/xiaomi-csv")
async def ingest_xiaomi_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Xiaomi Mi Smart Band 10 Pro data parsing pipeline not yet implemented.")

@router.post("/xiaomi-json")
async def ingest_xiaomi_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Xiaomi Mi Smart Band 10 Pro data parsing pipeline not yet implemented.")

@router.post("/strava")
async def ingest_strava(data: dict, db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Strava data ingestion pipeline not yet implemented.")

@router.get("/csv")
def export_csv(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Data export pipeline not yet implemented.")

@router.get("/json")
def export_json(start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Phase 2: Data export pipeline not yet implemented.")
