import pytest
from datetime import date, time, timedelta
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, Session, select, delete
from app.main import app
from app.core.db import get_db, engine
from app.models.domain_models import User as UserModel

# ── Test Database Setup ───────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_db():
    """Create an in-memory SQLite test database."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    sync_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        yield session


@pytest.fixture(autouse=True)
def clean_db(test_db: Session):
    """Truncate all tables between tests."""
    from app.models.domain_models import (
        StrengthSet, StrengthSession, DailyVitals, NutritionLog,
        InjuryLog, CardioSession, LifestyleSession, Conversation, LLMConfig,
    )
    tables = [LLMConfig, Conversation, InjuryLog, StrengthSet, CardioSession,
              LifestyleSession, StrengthSession, NutritionLog, DailyVitals, UserModel]
    for table in reversed(tables):
        test_db.exec(delete(table)).execute()
    test_db.commit()


@pytest.fixture
async def client(test_db):
    """HTTPX async client with test DB dependency injection."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


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
        "email": "test@example.com",
        "password": "securepass123",
    })
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login_test@example.com",
        "password": "securepass123",
    })
    resp = await client.post("/api/v1/auth/login", data={
        "username": "login_test@example.com",
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
        "username": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


# ── Daily Vitals Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_vital(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "vital@test.com", "password": "testpass123"
    })
    token = _get_token(reg)

    today = date.today().isoformat()
    resp = await client.post(f"/api/v1/vitals/", json={
        "date": today,
        "sleep_total_hours": 7.5,
        "resting_heart_rate": 58,
        "morning_weight_kg": 82.3,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["date"] == today
    assert data["sleep_total_hours"] == 7.5


@pytest.mark.asyncio
async def test_create_duplicate_vital(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    await client.post(f"/api/v1/vitals/", json={
        "date": today, "sleep_total_hours": 6.0
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.post(f"/api/v1/vitals/", json={
        "date": today, "sleep_total_hours": 7.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_read_vital(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "rd@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    await client.post(f"/api/v1/vitals/", json={
        "date": today, "sleep_total_hours": 8.0
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.get(f"/api/v1/vitals/{today}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sleep_total_hours"] == 8.0


@pytest.mark.asyncio
async def test_update_vital(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "upd@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    await client.post(f"/api/v1/vitals/", json={
        "date": today, "sleep_total_hours": 6.0
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.put(f"/api/v1/vitals/{today}", json={
        "sleep_total_hours": 9.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sleep_total_hours"] == 9.0


@pytest.mark.asyncio
async def test_list_vitals(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "lst@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()

    await client.post(f"/api/v1/vitals/", json={"date": yesterday, "sleep_total_hours": 5.0},
                      headers={"Authorization": f"Bearer {token}"})
    await client.post(f"/api/v1/vitals/", json={"date": today.isoformat(), "sleep_total_hours": 7.0},
                      headers={"Authorization": f"Bearer {token}"})

    resp = await client.get("/api/v1/vitals/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_delete_vital(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "del@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    await client.post(f"/api/v1/vitals/", json={"date": today},
                      headers={"Authorization": f"Bearer {token}"})
    resp = await client.delete(f"/api/v1/vitals/{today}",
                               headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ── Strength Session Tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_strength_session(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "str@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/strength/", json={
        "date": today,
        "session_focus": "Push",
        "location": "Gym",
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
    reg = await client.post("/api/v1/auth/register", json={
        "email": "sr@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/strength/", json={
        "date": today, "session_focus": "Legs"
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/strength/{session_id}",
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["session_focus"] == "Legs"


@pytest.mark.asyncio
async def test_update_strength_session(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "su@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/strength/", json={
        "date": today, "session_focus": "Pull"
    }, headers={"Authorization": f"Bearer {token}"})
    session_id = resp.json()["id"]

    resp = await client.put(f"/api/v1/strength/{session_id}", json={
        "session_focus": "Legs"
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["session_focus"] == "Legs"


# ── Cardio Session Tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_cardio(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "cardio@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/cardio/", json={
        "date": today,
        "activity_type": "Run",
        "duration_minutes": 30.0,
        "distance_km": 5.0,
        "average_heart_rate": 150,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["activity_type"] == "Run"
    assert data["distance_km"] == 5.0


# ── Lifestyle Session Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_lifestyle(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "life@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/lifestyle/", json={
        "date": today,
        "activity_type": "Salsa",
        "duration_minutes": 120.0,
        "average_heart_rate": 130,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["activity_type"] == "Salsa"


# ── Nutrition Log Tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_nutrition(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "nutri@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/nutrition/", json={
        "date": today,
        "espresso_count": 2,
        "water_liters": 3.0,
        "general_diet_quality": "Clean",
        "specific_meals_array": ["Prazma kralovska", "Racana"],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["espresso_count"] == 2
    assert "Prazma kralovska" in data["specific_meals_array"]


@pytest.mark.asyncio
async def test_update_nutrition(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "nutri2@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    await client.post("/api/v1/nutrition/", json={
        "date": today, "espresso_count": 1
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.put(f"/api/v1/nutrition/{today}", json={
        "espresso_count": 3
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["espresso_count"] == 3


# ── Injury Log Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_injury(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "inj@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    today = date.today().isoformat()

    resp = await client.post("/api/v1/injury/", json={
        "date_logged": today,
        "body_part": "Right shoulder",
        "status": "Sore",
        "pain_scale": 3,
        "training_modification_required": True,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["body_part"] == "Right shoulder"
    assert data["training_modification_required"] is True


# ── Ingest Stubs ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_xiaomi_csv_stub(client):
    from io import BytesIO
    resp = await client.post("/api/v1/ingest/xiaomi-csv", files={
        "file": ("test.csv", BytesIO(b"id,date,steps\n1,2024-01-01,10000"), "text/csv")
    })
    assert resp.status_code == 501
    assert "Phase 2" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_xiaomi_json_stub(client):
    from io import BytesIO
    resp = await client.post("/api/v1/ingest/xiaomi-json", files={
        "file": ("test.json", BytesIO(b'{}'), "application/json")
    })
    assert resp.status_code == 501
    assert "Phase 2" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_export_csv_stub(client):
    resp = await client.get("/api/v1/export/csv")
    assert resp.status_code == 501
    assert "Phase 2" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_export_json_stub(client):
    resp = await client.get("/api/v1/export/json")
    assert resp.status_code == 501
    assert "Phase 2" in resp.json()["detail"]


# ── Conversation Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_conversation(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "conv@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    user_id = reg.json()["id"]

    resp = await client.post("/api/v1/conversation/", json={
        "user_id": user_id,
        "session_type": "strength",
        "session_summary": "Push day was solid. Bench press felt heavy, shoulders okay.",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_type"] == "strength"


@pytest.mark.asyncio
async def test_get_conversation_history(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "hist@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    user_id = reg.json()["id"]

    await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "strength",
        "session_summary": "Day 1",
    }, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "cardio",
        "session_summary": "5k run",
    }, headers={"Authorization": f"Bearer {token}"})

    resp = await client.get(f"/api/v1/conversation/history?user_id={user_id}",
                            headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_delete_conversation(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "dconv@test.com", "password": "testpass123"
    })
    token = _get_token(reg)
    user_id = reg.json()["id"]

    resp = await client.post("/api/v1/conversation/", json={
        "user_id": user_id, "session_type": "strength",
        "session_summary": "Delete me",
    }, headers={"Authorization": f"Bearer {token}"})
    conv_id = resp.json()["id"]

    resp = await client.delete(f"/api/v1/conversation/{conv_id}",
                               headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_token(resp) -> str:
    if "access_token" in resp.json():
        return resp.json()["access_token"]
    return resp.json()["access_token"]
