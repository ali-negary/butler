from datetime import date, datetime, time
from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, Float as SAFloat, Integer as SAInteger, String as SAString, Boolean as SABoolean, JSON as SAJSON, Date as SADate, Time as SATime, Text


class DailyVitalsBase(SQLModel):
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


class DailyVitals(DailyVitalsBase, table=True):
    __tablename__ = "daily_vitals"

    date: date = Field(primary_key=True)
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))


class DailyVitalsRead(DailyVitalsBase):
    date: date
    id: int = Field(description="Internal read-only identifier")


class DailyVitalsCreate(DailyVitalsBase):
    pass


class DailyVitalsUpdate(SQLModel):
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


# Strength Session

class StrengthSessionBase(SQLModel):
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: str = "Gym"
    session_focus: str = "Full Body"
    perceived_exertion_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    session_notes: Optional[str] = None


class StrengthSession(StrengthSessionBase, table=True):
    __tablename__ = "strength_sessions"

    id: int = Field(default=None, primary_key=True)
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    sets: List["StrengthSet"] = Relationship(back_populates="session")


class StrengthSessionRead(StrengthSessionBase):
    id: int
    sets: List["StrengthSetRead"] = []


class StrengthSessionCreate(StrengthSessionBase):
    sets: Optional[List["StrengthSetCreate"]] = []


class StrengthSessionUpdate(SQLModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    session_focus: Optional[str] = None
    perceived_exertion_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    session_notes: Optional[str] = None


# Strength Set

class StrengthSetBase(SQLModel):
    exercise_name: str
    set_number: int
    weight_kg: float
    reps: int
    is_failure: bool = False
    notes: Optional[str] = None


class StrengthSet(StrengthSetBase, table=True):
    __tablename__ = "strength_sets"

    id: int = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="strength_sessions.id")
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    session: Optional[StrengthSession] = Relationship(back_populates="sets")


class StrengthSetRead(StrengthSetBase):
    id: int
    session_id: int


class StrengthSetCreate(StrengthSetBase):
    pass


class StrengthSetUpdate(SQLModel):
    exercise_name: Optional[str] = None
    set_number: Optional[int] = None
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    is_failure: Optional[bool] = None
    notes: Optional[str] = None


# Cardio Session

class CardioSessionBase(SQLModel):
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


class CardioSession(CardioSessionBase, table=True):
    __tablename__ = "cardio_sessions"

    id: int = Field(default=None, primary_key=True)
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))


class CardioSessionRead(CardioSessionBase):
    id: int


class CardioSessionCreate(CardioSessionBase):
    pass


class CardioSessionUpdate(SQLModel):
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


# Lifestyle Session

class LifestyleSessionBase(SQLModel):
    date: date
    start_time: Optional[time] = None
    duration_minutes: float
    activity_type: str = "General Social"
    average_heart_rate: Optional[int] = None
    perceived_fatigue_post_event: Optional[int] = Field(default=None, ge=1, le=10)


class LifestyleSession(LifestyleSessionBase, table=True):
    __tablename__ = "lifestyle_sessions"

    id: int = Field(default=None, primary_key=True)
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))


class LifestyleSessionRead(LifestyleSessionBase):
    id: int


class LifestyleSessionCreate(LifestyleSessionBase):
    pass


class LifestyleSessionUpdate(SQLModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    duration_minutes: Optional[float] = None
    activity_type: Optional[str] = None
    average_heart_rate: Optional[int] = None
    perceived_fatigue_post_event: Optional[int] = Field(default=None, ge=1, le=10)


# Nutrition Log

class NutritionLogBase(SQLModel):
    espresso_count: int = 0
    whey_protein_scoops: float = 0.0
    creatine_grams: float = 0.0
    water_liters: Optional[float] = None
    general_diet_quality: str = "Mixed"
    specific_meals_array: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))


class NutritionLog(NutritionLogBase, table=True):
    __tablename__ = "nutrition_logs"

    date: date = Field(primary_key=True)
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))


class NutritionLogRead(NutritionLogBase):
    date: date


class NutritionLogCreate(NutritionLogBase):
    pass


class NutritionLogUpdate(SQLModel):
    espresso_count: Optional[int] = None
    whey_protein_scoops: Optional[float] = None
    creatine_grams: Optional[float] = None
    water_liters: Optional[float] = None
    general_diet_quality: Optional[str] = None
    specific_meals_array: Optional[List[str]] = None


# Injury Log

class InjuryLogBase(SQLModel):
    date_logged: date
    body_part: str
    status: str = "Sore"
    pain_scale: int = Field(default=5, ge=1, le=10)
    training_modification_required: bool = False
    notes: Optional[str] = None


class InjuryLog(InjuryLogBase, table=True):
    __tablename__ = "injury_logs"

    id: int = Field(default=None, primary_key=True)
    created_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))
    updated_at: Optional[DateTime] = Field(default=None, sa_column=Column(DateTime))


class InjuryLogRead(InjuryLogBase):
    id: int


class InjuryLogCreate(InjuryLogBase):
    pass


class InjuryLogUpdate(SQLModel):
    body_part: Optional[str] = None
    status: Optional[str] = None
    pain_scale: Optional[int] = Field(default=None, ge=1, le=10)
    training_modification_required: Optional[bool] = None
    notes: Optional[str] = None


# User

class UserBase(SQLModel):
    email: str
    full_name: Optional[str] = None


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    hashed_password: str = Field(sa_column=Column(Text))
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime


class UserCreate(UserBase):
    password: str


# Conversation

class ConversationBase(SQLModel):
    session_summary: str
    llm_response: str


class Conversation(ConversationBase, table=True):
    __tablename__ = "conversations"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    session_type: Optional[str] = None
    session_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class ConversationRead(ConversationBase):
    id: int
    user_id: int
    session_type: Optional[str] = None
    session_id: Optional[int] = None
    created_at: datetime


class ConversationCreate(SQLModel):
    user_id: int
    session_type: Optional[str] = None
    session_id: Optional[int] = None
    session_summary: str


# LLM Config

class LLMConfigBase(SQLModel):
    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    api_key: str = Field(sa_column=Column(Text))
    system_prompt: Optional[str] = None


class LLMConfig(LLMConfigBase, table=True):
    __tablename__ = "llm_configs"

    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


class LLMConfigRead(LLMConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigUpdate(SQLModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    system_prompt: Optional[str] = None
