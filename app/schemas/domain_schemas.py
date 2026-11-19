from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date, datetime
from typing import Optional, List


# ── User ──────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


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
