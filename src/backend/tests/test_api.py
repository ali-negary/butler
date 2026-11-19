import pytest
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, select, delete
from app.models.domain_models import (
    StrengthSet, StrengthSession, DailyVitals, NutritionLog,
    InjuryLog, CardioSession, LifestyleSession, Conversation, LLMConfig,
    User as UserModel,
)

test_sync_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    SQLModel.metadata.create_all(test_sync_engine)
    yield


@pytest.fixture()
def test_db():
    with Session(test_sync_engine) as session:
        yield session
        session.rollback()
        for table in reversed([
            LLMConfig, Conversation, InjuryLog, StrengthSet, CardioSession,
            LifestyleSession, StrengthSession, NutritionLog, DailyVitals, UserModel,
        ]):
            session.execute(delete(table))
        session.commit()


@pytest.fixture()
async def client(test_db):
    from app.main import app
    from app.core.db import get_db

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _register_and_login(ac, email=None):
    if email is None:
        email = f"<PII_EMAIL_{email or 'abc123'}>"
    await ac.post("/api/v1/auth/register", json={
        "email": email, "password": "testpass123"
    })
    r = await ac.post("/api/v1/auth/login", data={"email": email, "password": "testpass123"})
    return r.json()["access_token"]


# ── Auth Tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "securepass123",
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "securepass123",
    })
    resp = await client.post("/api/v1/auth/login", data={
        "email": "login@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "password": "securepass123",
    })
    resp = await client.post("/api/v1/auth/login", data={
        "email": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


# ── Vitals ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_vital(client):
    token = _register_and_login(client, "vital1")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/vitals/", json={
        "date": today, "sleep_total_hours": 7.5,
        "resting_heart_rate": 58, "morning_weight_kg": 82.3,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["date"] == today


@pytest.mark.asyncio
async def test_create_duplicate_vital(client):
    token = _register_and_login(client, "dup1")
    today = date.today().isoformat()
    await client.post("/api/v1/vitals/", json={"date": today, "sleep_total_hours": 6.0},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.post("/api/v1/vitals/", json={"date": today, "sleep_total_hours": 7.0},
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_read_vital(client):
    token = _register_and_login(client, "read1")
    today = date.today().isoformat()
    await client.post("/api/v1/vitals/", json={"date": today, "sleep_total_hours": 8.0},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.get(f"/api/v1/vitals/{today}", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["sleep_total_hours"] == 8.0


@pytest.mark.asyncio
async def test_update_vital(client):
    token = _register_and_login(client, "upd1")
    today = date.today().isoformat()
    await client.post("/api/v1/vitals/", json={"date": today, "sleep_total_hours": 6.0},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.put(f"/api/v1/vitals/{today}", json={"sleep_total_hours": 9.0},
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["sleep_total_hours"] == 9.0


@pytest.mark.asyncio
async def test_list_vitals(client):
    token = _register_and_login(client, "list1")
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    await client.post("/api/v1/vitals/", json={"date": yesterday, "sleep_total_hours": 5.0},
                      headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/vitals/", json={"date": today.isoformat(), "sleep_total_hours": 7.0},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.get("/api/v1/vitals/", headers={"Authorization": f"Bearer {token}"})
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_delete_vital(client):
    token = _register_and_login(client, "del1")
    today = date.today().isoformat()
    await client.post("/api/v1/vitals/", json={"date": today},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.delete(f"/api/v1/vitals/{today}",
                               headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["ok"] is True


# ── Strength ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_strength_session(client):
    token = _register_and_login(client, "str1")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/strength/", json={
        "date": today, "session_focus": "Push", "location": "Gym",
        "perceived_exertion_rpe": 8,
        "sets": [
            {"exercise_name": "Bench Press", "set_number": 1, "weight_kg": 80, "reps": 8},
            {"exercise_name": "Bench Press", "set_number": 2, "weight_kg": 80, "reps": 7},
        ],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_focus"] == "Push"
    assert len(data["sets"]) == 2


@pytest.mark.asyncio
async def test_read_strength_session(client):
    token = _register_and_login(client, "str2")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/strength/", json={
        "date": today, "session_focus": "Legs"
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.get(f"/api/v1/strength/{session_id}",
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["session_focus"] == "Legs"


@pytest.mark.asyncio
async def test_update_strength_session(client):
    token = _register_and_login(client, "str3")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/strength/", json={
        "date": today, "session_focus": "Pull"
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.put(f"/api/v1/strength/{session_id}", json={"session_focus": "Legs"},
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["session_focus"] == "Legs"


@pytest.mark.asyncio
async def test_create_strength_set(client):
    token = _register_and_login(client, "str4")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/strength/", json={"date": today},
                             headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.post(f"/api/v1/strength/{session_id}/sets/", json={
        "exercise_name": "Bicep Curls", "set_number": 1, "weight_kg": 15, "reps": 12
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["exercise_name"] == "Bicep Curls"


@pytest.mark.asyncio
async def test_update_strength_set(client):
    token = _register_and_login(client, "str5")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/strength/", json={"date": today},
                             headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.post(f"/api/v1/strength/{session_id}/sets/", json={
        "exercise_name": "Tricep Dips", "set_number": 1, "weight_kg": 0, "reps": 10
    }, headers={"Authorization": f"Bearer {token}"})
    set_id = resp.json()["id"]
    resp = await client.put(f"/api/v1/strength/sets/{set_id}", json={"reps": 15},
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["reps"] == 15


# ── Cardio ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_cardio(client):
    token = _register_and_login(client, "car1")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/cardio/", json={
        "date": today, "activity_type": "Run", "duration_minutes": 30.0,
        "distance_km": 5.0, "average_heart_rate": 150,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["distance_km"] == 5.0


@pytest.mark.asyncio
async def test_update_cardio(client):
    token = _register_and_login(client, "car2")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/cardio/", json={
        "date": today, "activity_type": "Run", "duration_minutes": 30.0
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.put(f"/api/v1/cardio/{session_id}", json={"activity_type": "Walk"},
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["activity_type"] == "Walk"


@pytest.mark.asyncio
async def test_delete_cardio(client):
    token = _register_and_login(client, "car3")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/cardio/", json={
        "date": today, "activity_type": "Run", "duration_minutes": 30.0
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.delete(f"/api/v1/cardio/{session_id}",
                               headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


# ── Lifestyle ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_lifestyle(client):
    token = _register_and_login(client, "lfs1")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/lifestyle/", json={
        "date": today, "activity_type": "Salsa", "duration_minutes": 120.0,
        "average_heart_rate": 130,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["activity_type"] == "Salsa"


@pytest.mark.asyncio
async def test_update_lifestyle(client):
    token = _register_and_login(client, "lfs2")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/lifestyle/", json={
        "date": today, "activity_type": "Salsa", "duration_minutes": 120.0
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]
    resp = await client.put(f"/api/v1/lifestyle/{session_id}", json={"activity_type": "Forro"},
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["activity_type"] == "Forro"


# ── Nutrition ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_nutrition(client):
    token = _register_and_login(client, "nut1")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/nutrition/", json={
        "date": today, "espresso_count": 2, "water_liters": 3.0,
        "general_diet_quality": "Clean",
        "specific_meals_array": ["Prazma kralovska", "Racana"],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["espresso_count"] == 2
    assert "Prazma kralovska" in resp.json()["specific_meals_array"]


@pytest.mark.asyncio
async def test_update_nutrition(client):
    token = _register_and_login(client, "nut2")
    today = date.today().isoformat()
    await client.post("/api/v1/nutrition/", json={"date": today, "espresso_count": 1},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.put(f"/api/v1/nutrition/{today}", json={"espresso_count": 3},
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["espresso_count"] == 3


@pytest.mark.asyncio
async def test_delete_nutrition(client):
    token = _register_and_login(client, "nut3")
    today = date.today().isoformat()
    await client.post("/api/v1/nutrition/", json={"date": today, "espresso_count": 1},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.delete(f"/api/v1/nutrition/{today}",
                               headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


# ── Injury ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_injury(client):
    token = _register_and_login(client, "inj1")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/injury/", json={
        "date_logged": today, "body_part": "Right shoulder",
        "status": "Sore", "pain_scale": 3,
        "training_modification_required": True,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["training_modification_required"] is True


@pytest.mark.asyncio
async def test_update_injury(client):
    token = _register_and_login(client, "inj2")
    today = date.today().isoformat()
    resp = await client.post("/api/v1/injury/", json={
        "date_logged": today, "body_part": "Knee", "status": "Strained", "pain_scale": 6
    }, headers={"Authorization": f"Bearer {token}"})
    log_id = resp.json()["id"]
    resp = await client.put(f"/api/v1/injury/{log_id}", json={
        "status": "Recovering", "pain_scale": 2
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["status"] == "Recovering"


# ── Ingest Stubs ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_xiaomi_csv_stub(client):
    from io import BytesIO
    resp = await client.post("/api/v1/ingest/xiaomi-csv", files={
        "file": ("test.csv", BytesIO(b"id,date,steps\n1,2024-01-01,10000"), "text/csv")
    })
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_ingest_xiaomi_json_stub(client):
    from io import BytesIO
    resp = await client.post("/api/v1/ingest/xiaomi-json", files={
        "file": ("test.json", BytesIO(b'{}'), "application/json")
    })
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_export_csv_stub(client):
    resp = await client.get("/api/v1/export/csv")
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_export_json_stub(client):
    resp = await client.get("/api/v1/export/json")
    assert resp.status_code == 501


# ── Conversation ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_conversation(client):
    token = await _register_and_login(client, "conv1")
    r = await client.post("/api/v1/auth/register", json={"email": "<PII_EMAIL_a>", "password": "testpass123"})
    user_id = r.json()["id"]
    resp = await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "strength",
        "session_summary": "Push day was solid.",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["session_type"] == "strength"


@pytest.mark.asyncio
async def test_get_conversation_history(client):
    token = await _register_and_login(client, "conv2")
    r = await client.post("/api/v1/auth/register", json={"email": "<PII_EMAIL_b>", "password": "testpass123"})
    user_id = r.json()["id"]
    await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "strength", "session_summary": "Day 1",
    }, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "cardio", "session_summary": "5k run",
    }, headers={"Authorization": f"Bearer {token}"})
    resp = await client.get(f"/api/v1/conversation/history?user_id={user_id}",
                            headers={"Authorization": f"Bearer {token}"})
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_delete_conversation(client):
    token = await _register_and_login(client, "conv3")
    r = await client.post("/api/v1/auth/register", json={"email": "<PII_EMAIL_c>", "password": "testpass123"})
    user_id = r.json()["id"]
    resp = await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "strength", "session_summary": "Delete me",
    }, headers={"Authorization": f"Bearer {token}"})
    conv_id = resp.json()["id"]
    resp = await client.delete(f"/api/v1/conversation/{conv_id}",
                               headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
