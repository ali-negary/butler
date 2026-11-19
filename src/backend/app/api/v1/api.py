from fastapi import APIRouter
from app.api.v1.endpoints import vitals, strength, cardio, lifestyle, nutrition, injury, auth, ingest, export, conversation

api_router = APIRouter()

api_router.include_router(vitals.router, prefix="/vitals", tags=["vitals"])
api_router.include_router(strength.router, prefix="/strength", tags=["strength"])
api_router.include_router(cardio.router, prefix="/cardio", tags=["cardio"])
api_router.include_router(lifestyle.router, prefix="/lifestyle", tags=["lifestyle"])
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["nutrition"])
api_router.include_router(injury.router, prefix="/injury", tags=["injury"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
