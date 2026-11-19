from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import List, Optional
import httpx

from app.core.config import get_settings
from app.models.domain_models import Conversation as ConversationModel
from app.schemas.domain_schemas import ConversationCreate, ConversationRead
from app.api.dependencies import get_db, get_current_user

settings = get_settings()
router = APIRouter()


async def _call_llm(prompt: str, user_conv: Optional[str] = None) -> str:
    """Call OpenAI if API key is configured, otherwise return a placeholder."""
    if not settings.openai_api_key:
        return "🤖 Butler: LLM not configured. Set OPENAI_API_KEY in your .env file to enable AI responses."

    system_prompt = (
        "You are Butler, a personal health and fitness coach. "
        "You analyze the user's vitals, workouts, nutrition, and injuries "
        "to give actionable, evidence-based advice. Be concise and practical."
    )
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if user_conv:
        messages.append({"role": "user", "content": user_conv})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            json={"model": "gpt-4o-mini", "messages": messages, "max_tokens": 500},
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"⚠️ LLM error: {exc}"


@router.post("/", response_model=ConversationRead, status_code=201)
async def create_conversation(conv: ConversationCreate, db: Session = Depends(get_db)):
    llm_response = ""
    if conv.session_summary and conv.llm_response is not None and not conv.llm_response:
        llm_response = await _call_llm(conv.session_summary)

    db_conv = ConversationModel(
        user_id=conv.user_id,
        session_type=conv.session_type,
        session_id=conv.session_id,
        session_summary=conv.session_summary,
        llm_response=llm_response or conv.llm_response or "",
    )
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv


@router.get("/history", response_model=List[ConversationRead])
def get_conversation_history(
    user_id: int,
    session_type: Optional[str] = None,
    limit: int = 50,
    current_user: Optional[object] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(ConversationModel).where(ConversationModel.user_id == user_id)
    if session_type:
        stmt = stmt.where(ConversationModel.session_type == session_type)
    stmt = stmt.order_by(desc(ConversationModel.created_at)).limit(limit)
    return list(db.exec(stmt).all())


@router.delete("/{conv_id}")
def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    db_conv = db.get(ConversationModel, conv_id)
    if not db_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(db_conv)
    db.commit()
    return {"ok": True}


@router.post("/ask", response_model=ConversationRead, status_code=201)
async def ask_butler(prompt: str, db: Session = Depends(get_db)):
    """Quick ask — creates a conversation entry with LLM response."""
    response = await _call_llm(prompt)
    db_conv = ConversationModel(
        user_id=0,
        session_type="ask",
        session_summary=prompt,
        llm_response=response,
    )
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv
