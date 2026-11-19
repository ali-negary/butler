"""
Project Butler - Personal Health & Fitness API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.core.config import get_settings
from app.core.db import get_sync_engine
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    SQLModel.metadata.create_all(get_sync_engine())
    yield


app = FastAPI(
    title="Project Butler",
    description="Personal Health & Fitness Tracking API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
