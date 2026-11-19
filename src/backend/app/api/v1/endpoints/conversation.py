from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import List, Optional
from app.models.domain_models import Conversation as ConversationModel
from app.schemas.domain_schemas import ConversationCreate, ConversationRead
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=ConversationRead, status_code=201)
def create_conversation(conv: ConversationCreate, db: Session = Depends(get_db)):
    db_conv = ConversationModel.model_validate(conv)
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv

@router.get("/history", response_model=List[ConversationRead])
def get_conversation_history(user_id: int, session_type: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
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
