from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime, time
from typing import Optional, List


# ── Daily Vitals ──────────────────────────────────────────────────────────

class DailyVitalsBase(BaseModel):
    sleep_total_hours: Optional[float] = None
    sleep_deep_hours: Optional[float] = None
    sleep_rem_hours: Optional[float] = None
    resting_heart_rate: Optional[int] = None
    hrv_score: Optional[int] = None
    average_blood_oxygen: Optional[float] = None
    daily_stress_score: Optional[int] = None
    total_daily_steps: Optional[int] = None
    total_calories_burned: Optional[int] = None
    morning_weight_kg: Optional[float] = None


class DailyVitalsCreate(DailyVitalsBase):
    date: date


class DailyVitalsRead(DailyVitalsBase):
    date: date

    model_config = ConfigDict(from_attributes=True)


class DailyVitalsUpdate(BaseModel):
    sleep_total_hours: Optional[float] = None
    sleep_deep_hours: Optional[float] = None
    sleep_rem_hours: Optional[float] = None
    resting_heart_rate: Optional[int] = None
    hrv_score: Optional[int] = None
    average_blood_oxygen: Optional[float] = None
    daily_stress_score: Optional[int] = None
    total_daily_steps: Optional[int] = None
    total_calories_burned: Optional[int] = None
    morning_weight_kg: Optional[float] = None


# ── Strength Session ──────────────────────────────────────────────────────

class StrengthSessionBase(BaseModel):
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: str = "Gym"
    session_focus: str = "Full Body"
    perceived_exertion_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    session_notes: Optional[str] = None


class StrengthSessionCreate(StrengthSessionBase):
    sets: Optional[List["StrengthSetCreate"]] = None


class StrengthSessionRead(StrengthSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    sets: List["StrengthSetRead"] = []

    model_config = ConfigDict(from_attributes=True)


class StrengthSessionUpdate(BaseModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    session_focus: Optional[str] = None
    perceived_exertion_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    session_notes: Optional[str] = None


# ── Strength Set ──────────────────────────────────────────────────────────

class StrengthSetBase(BaseModel):
    exercise_name: str
    set_number: int
    weight_kg: float
    reps: int
    is_failure: bool = False
    notes: Optional[str] = None


class StrengthSetCreate(StrengthSetBase):
    pass


class StrengthSetRead(StrengthSetBase):
    id: int
    session_id: int

    model_config = ConfigDict(from_attributes=True)


class StrengthSetUpdate(BaseModel):
    exercise_name: Optional[str] = None
    set_number: Optional[int] = None
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    is_failure: Optional[bool] = None
    notes: Optional[str] = None


# ── Cardio ────────────────────────────────────────────────────────────────

class CardioSessionBase(BaseModel):
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    activity_type: str = "Run"
    duration_minutes: float
    distance_km: Optional[float] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    incline_or_elevation_gain: Optional[float] = None
    average_pace_kmh: Optional[float] = None
    notes: Optional[str] = None


class CardioSessionCreate(CardioSessionBase):
    pass


class CardioSessionRead(CardioSessionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CardioSessionUpdate(BaseModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    activity_type: Optional[str] = None
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    average_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    incline_or_elevation_gain: Optional[float] = None
    average_pace_kmh: Optional[float] = None
    notes: Optional[str] = None


# ── Lifestyle ─────────────────────────────────────────────────────────────

class LifestyleSessionBase(BaseModel):
    date: date
    start_time: Optional[time] = None
    duration_minutes: float
    activity_type: str = "General Social"
    average_heart_rate: Optional[int] = None
    perceived_fatigue_post_event: Optional[int] = Field(default=None, ge=1, le=10)


class LifestyleSessionCreate(LifestyleSessionBase):
    pass


class LifestyleSessionRead(LifestyleSessionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LifestyleSessionUpdate(BaseModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    duration_minutes: Optional[float] = None
    activity_type: Optional[str] = None
    average_heart_rate: Optional[int] = None
    perceived_fatigue_post_event: Optional[int] = Field(default=None, ge=1, le=10)


# ── Nutrition ─────────────────────────────────────────────────────────────

class NutritionLogBase(BaseModel):
    espresso_count: int = 0
    whey_protein_scoops: float = 0.0
    creatine_grams: float = 0.0
    water_liters: Optional[float] = None
    general_diet_quality: str = "Mixed"
    specific_meals_array: Optional[List[str]] = None


class NutritionLogCreate(NutritionLogBase):
    date: date


class NutritionLogRead(NutritionLogBase):
    date: date

    model_config = ConfigDict(from_attributes=True)


class NutritionLogUpdate(BaseModel):
    espresso_count: Optional[int] = None
    whey_protein_scoops: Optional[float] = None
    creatine_grams: Optional[float] = None
    water_liters: Optional[float] = None
    general_diet_quality: Optional[str] = None
    specific_meals_array: Optional[List[str]] = None


# ── Injury ────────────────────────────────────────────────────────────────

class InjuryLogBase(BaseModel):
    date_logged: date
    body_part: str
    status: str = "Sore"
    pain_scale: int = Field(default=5, ge=1, le=10)
    training_modification_required: bool = False
    notes: Optional[str] = None


class InjuryLogCreate(InjuryLogBase):
    pass


class InjuryLogRead(InjuryLogBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class InjuryLogUpdate(BaseModel):
    body_part: Optional[str] = None
    status: Optional[str] = None
    pain_scale: Optional[int] = Field(default=None, ge=1, le=10)
    training_modification_required: Optional[bool] = None
    notes: Optional[str] = None


# ── User ──────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ── Conversation ──────────────────────────────────────────────────────────

class ConversationBase(BaseModel):
    session_summary: str
    llm_response: str


class ConversationCreate(BaseModel):
    user_id: int
    session_type: Optional[str] = None
    session_id: Optional[int] = None
    session_summary: str
    llm_response: str = ""


class ConversationRead(ConversationBase):
    id: int
    user_id: int
    session_type: Optional[str] = None
    session_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── LLM Config ────────────────────────────────────────────────────────────

class LLMConfigBase(BaseModel):
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    api_key: str
    system_prompt: Optional[str] = None


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigRead(LLMConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    system_prompt: Optional[str] = None
