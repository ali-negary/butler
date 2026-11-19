from fastapi import APIRouter
from app.api.v1.endpoints import vitals, auth, ingest, conversation

api_router = APIRouter()

api_router.include_router(vitals.router, prefix="/vitals", tags=["vitals"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
