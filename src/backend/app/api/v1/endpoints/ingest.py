import csv
import io
import uuid
from datetime import datetime, timezone, date as _date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from sqlmodel import Session, select
import httpx

from app.core.config import get_settings
from app.models.domain_models import (
    DailyVitals, StrengthSession, StrengthSet, CardioSession,
    LifestyleSession, NutritionLog, InjuryLog, Conversation,
)
from app.schemas.domain_schemas import (
    DailyVitalsRead, StrengthSessionRead, StrengthSetRead,
    CardioSessionRead, LifestyleSessionRead, NutritionLogRead,
    InjuryLogRead, ConversationRead,
)
from app.api.dependencies import get_db

settings = get_settings()
router = APIRouter()


# ──────────────────────────────────────────────
#  Xiaomi CSV Import (Mi Fit / Health Sync format)
# ──────────────────────────────────────────────

@router.post("/xiaomi-csv", summary="Import daily vitals from Xiaomi Health/Health Sync CSV")
def ingest_xiaomi_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    created = []
    for row in reader:
        date_str = None
        for key in ("date", "date_log", "day", "day_log"):
            if key in row and row[key]:
                date_str = row[key]
                break
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str)
            d = dt.date()
        except Exception:
            try:
                d = _date.fromisoformat(date_str[:10])
            except Exception:
                continue

        existing = db.get(DailyVitals, d)
        if existing:
            continue

        def _float(val):
            try:
                v = float(val)
                return v if v > 0 else None
            except (ValueError, TypeError):
                return None

        def _int(val):
            try:
                v = int(float(val))
                return v if v > 0 else None
            except (ValueError, TypeError):
                return None

        vital = DailyVitals(
            date=d,
            sleep_total_hours=_float(row.get("sleep_total_hours", row.get("total_sleep_hours", row.get("sleep")))),
            resting_heart_rate=_int(row.get("resting_heart_rate", row.get("heart_rate"))),
            hrv_score=_int(row.get("hrv")),
            average_blood_oxygen=_float(row.get("average_blood_oxygen", row.get("spo2"))),
            daily_stress_score=_int(row.get("daily_stress_score", row.get("stress"))),
            total_daily_steps=_int(row.get("total_daily_steps", row.get("steps"))),
            total_calories_burned=_int(row.get("total_calories_burned", row.get("calories"))),
            morning_weight_kg=_float(row.get("morning_weight_kg", row.get("weight"))),
        )
        if (vital.sleep_total_hours or vital.resting_heart_rate or vital.total_daily_steps
                or vital.morning_weight_kg or vital.hrv_score or vital.average_blood_oxygen):
            db.add(vital)
            created.append(d.isoformat())
    if created:
        db.commit()
    return {"ingested": len(created), "dates": created}


# ──────────────────────────────────────────────
#  Strava Import (OAuth + API)
# ──────────────────────────────────────────────

@router.get("/strava/callback")
def strava_callback(code: str, db: Session = Depends(get_db)):
    """Exchange Strava auth code for access/refresh tokens."""
    if not code:
        raise HTTPException(400, "Authorization code required")
    body = {
        "code": code,
        "client_id": settings.strava_client_id,
        "client_secret": settings.strava_client_secret,
        "grant_type": "authorization_code",
    }
    try:
        resp = httpx.post("https://www.strava.com/oauth/token", data=body, timeout=15)
        resp.raise_for_status()
        tokens = resp.json()
        return {"status": "success", "tokens": tokens}
    except Exception as exc:
        raise HTTPException(502, f"Strava token exchange failed: {exc}")


@router.post("/strava/sync")
def strava_sync(db: Session = Depends(get_db), access_token: Optional[str] = None):
    """Pull recent Strava activities (requires access_token query param or bearer)."""
    tok = access_token or settings.strava_access_token
    if not tok:
        raise HTTPException(400, "strava_access_token required. Obtain via /strava/callback")
    headers = {"Authorization": f"Bearer {tok}"}
    created = []
    try:
        resp = httpx.get("https://www.strava.com/api/v3/athlete/activities",
                          headers=headers, params={"per_page": 30}, timeout=30)
        resp.raise_for_status()
        activities = resp.json()
        for act in activities:
            date_str = act.get("start_date") or act.get("start_date_local")
            if not date_str:
                continue
            try:
                d = datetime.fromisoformat(date_str[:10]).date() if len(date_str) >= 10 else _date.fromisoformat(date_str[:10])
            except Exception:
                continue

            if db.get(CardioSession, d):
                continue

            duration_s = act.get("distance", 0) or act.get("total_elevation_gain", 0)
            km = round(act.get("distance", 0) / 1000, 2) if act.get("distance") else None
            hrs = round(act.get("moving_time", 0) / 3600, 2) if act.get("moving_time") else None

            cardio = CardioSession(
                date=d,
                activity_type=act.get("type", "Run"),
                duration_minutes=hrs * 60 if hrs else act.get("elapsed_time", 0),
                distance_km=km,
                average_heart_rate=act.get("average_heartrate") or act.get("average_heartrate"),
                max_heart_rate=act.get("max_heartrate"),
                notes=act.get("description"),
            )
            db.add(cardio)
            created.append(d.isoformat())
        db.commit()
    except Exception as exc:
        raise HTTPException(502, f"Strava sync failed: {exc}")
    return {"ingested": len(created), "dates": created}


# ──────────────────────────────────────────────
#  Export: CSV
# ──────────────────────────────────────────────

@router.get("/csv")
def export_csv(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    buf = io.StringIO()
    writer = csv.writer(buf)

    # DailyVitals
    writer.writerow(["type", "date", "sleep_total_hours", "sleep_deep_hours",
                      "resting_heart_rate", "hrv_score", "average_blood_oxygen",
                      "daily_stress_score", "total_daily_steps", "total_calories_burned",
                      "morning_weight_kg"])
    stmt = select(DailyVitals)
    if start_date: stmt = stmt.where(DailyVitals.date >= _date.fromisoformat(start_date))
    if end_date: stmt = stmt.where(DailyVitals.date <= _date.fromisoformat(end_date))
    for v in db.exec(stmt).all():
        writer.writerow([
            "vitals", v.date.isoformat(), v.sleep_total_hours, v.sleep_deep_hours,
            v.resting_heart_rate, v.hrv_score, v.average_blood_oxygen,
            v.daily_stress_score, v.total_daily_steps, v.total_calories_burned,
            v.morning_weight_kg,
        ])

    # Strength
    writer.writerow(["type", "date", "session_focus", "location", "session_notes",
                      "exercise_name", "set_number", "weight_kg", "reps"])
    stmt2 = select(StrengthSession).order_by(StrengthSession.date)
    if start_date: stmt2 = stmt2.where(StrengthSession.date >= _date.fromisoformat(start_date))
    if end_date: stmt2 = stmt2.where(StrengthSession.date <= _date.fromisoformat(end_date))
    for s in db.exec(stmt2).all():
        for set_item in (s.sets or []):
            writer.writerow(["strength", s.date.isoformat(), s.session_focus, s.location,
                             s.session_notes, set_item.exercise_name, set_item.set_number,
                             set_item.weight_kg, set_item.reps])

    # Cardio
    writer.writerow(["type", "date", "activity_type", "duration_minutes", "distance_km",
                      "average_heart_rate", "max_heart_rate", "notes"])
    stmt3 = select(CardioSession).order_by(CardioSession.date)
    if start_date: stmt3 = stmt3.where(CardioSession.date >= _date.fromisoformat(start_date))
    if end_date: stmt3 = stmt3.where(CardioSession.date <= _date.fromisoformat(end_date))
    for c in db.exec(stmt3).all():
        writer.writerow(["cardio", c.date.isoformat(), c.activity_type, c.duration_minutes,
                         c.distance_km, c.average_heart_rate, c.max_heart_rate, c.notes])

    # Lifestyle
    writer.writerow(["type", "date", "session_type", "duration_minutes", "notes"])
    stmt4 = select(LifestyleSession).order_by(LifestyleSession.date)
    if start_date: stmt4 = stmt4.where(LifestyleSession.date >= _date.fromisoformat(start_date))
    if end_date: stmt4 = stmt4.where(LifestyleSession.date <= _date.fromisoformat(end_date))
    for l in db.exec(stmt4).all():
        writer.writerow(["lifestyle", l.date.isoformat(), l.session_type, l.duration_minutes, l.notes])

    # Nutrition
    writer.writerow(["type", "date", "espresso_count", "whey_protein_scoops", "creatine_grams",
                      "water_liters", "general_diet_quality", "notes"])
    stmt5 = select(NutritionLog).order_by(NutritionLog.date)
    if start_date: stmt5 = stmt5.where(NutritionLog.date >= _date.fromisoformat(start_date))
    if end_date: stmt5 = stmt5.where(NutritionLog.date <= _date.fromisoformat(end_date))
    for n in db.exec(stmt5).all():
        writer.writerow(["nutrition", n.date.isoformat(), n.espresso_count, n.whey_protein_scoops,
                         n.creatine_grams, n.water_liters, n.general_diet_quality, n.notes])

    # Injury
    writer.writerow(["type", "date_logged", "body_part", "status", "pain_scale",
                      "training_modification_required", "notes"])
    for inj in db.exec(select(InjuryLog)).all():
        writer.writerow(["injury", inj.date_logged.isoformat(), inj.body_part, inj.status,
                         inj.pain_scale, inj.training_modification_required, inj.notes])

    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=project-butler-export.csv"},
    )


# ──────────────────────────────────────────────
#  Xiaomi JSON Import (placeholder)
# ──────────────────────────────────────────────

@router.post("/xiaomi-json")
def ingest_xiaomi_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return JSONResponse(status_code=501, content={"detail": "Phase 2: Xiaomi JSON ingestion not yet implemented."})


# ──────────────────────────────────────────────
#  Export: JSON
# ──────────────────────────────────────────────

@router.get("/json")
def export_json(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    from app.schemas.domain_schemas import (
        DailyVitalsRead as DVR,
        StrengthSessionRead as SSR,
        CardioSessionRead as CSR,
        LifestyleSessionRead as LSR,
        NutritionLogRead as NLR,
        InjuryLogRead as IIR,
    )

    result = {"daily_vitals": [], "strength_sessions": [], "cardio_sessions": [],
              "lifestyle_sessions": [], "nutrition_logs": [], "injury_logs": []}

    stmt1 = select(DailyVitals)
    if start_date: stmt1 = stmt1.where(DailyVitals.date >= _date.fromisoformat(start_date))
    if end_date: stmt1 = stmt1.where(DailyVitals.date <= _date.fromisoformat(end_date))
    result["daily_vitals"] = [DVR.model_validate(v).model_dump(mode="json") for v in db.exec(stmt1).all()]

    stmt2 = select(StrengthSession).order_by(StrengthSession.date)
    if start_date: stmt2 = stmt2.where(StrengthSession.date >= _date.fromisoformat(start_date))
    if end_date: stmt2 = stmt2.where(StrengthSession.date <= _date.fromisoformat(end_date))
    for s in db.exec(stmt2).all():
        db.expunge(s)
        item = SSR.model_validate(s).model_dump(mode="json")
        item["sets"] = [StrengthSetRead.model_validate(s2).model_dump(mode="json") for s2 in (s.sets or [])]
        result["strength_sessions"].append(item)

    stmt3 = select(CardioSession).order_by(CardioSession.date)
    if start_date: stmt3 = stmt3.where(CardioSession.date >= _date.fromisoformat(start_date))
    if end_date: stmt3 = stmt3.where(CardioSession.date <= _date.fromisoformat(end_date))
    result["cardio_sessions"] = [CSR.model_validate(c).model_dump(mode="json") for c in db.exec(stmt3).all()]

    stmt4 = select(LifestyleSession).order_by(LifestyleSession.date)
    if start_date: stmt4 = stmt4.where(LifestyleSession.date >= _date.fromisoformat(start_date))
    if end_date: stmt4 = stmt4.where(LifestyleSession.date <= _date.fromisoformat(end_date))
    result["lifestyle_sessions"] = [LSR.model_validate(l).model_dump(mode="json") for l in db.exec(stmt4).all()]

    stmt5 = select(NutritionLog).order_by(NutritionLog.date)
    if start_date: stmt5 = stmt5.where(NutritionLog.date >= _date.fromisoformat(start_date))
    if end_date: stmt5 = stmt5.where(NutritionLog.date <= _date.fromisoformat(end_date))
    result["nutrition_logs"] = [NLR.model_validate(n).model_dump(mode="json") for n in db.exec(stmt5).all()]

    for inj in db.exec(select(InjuryLog)).all():
        db.expunge(inj)
        result["injury_logs"].append(IIR.model_validate(inj).model_dump(mode="json"))

    db.close()
    return JSONResponse(content=result)
