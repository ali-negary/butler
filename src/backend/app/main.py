"""
Project Butler - Personal Health & Fitness API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from app.core.config import get_settings
from app.core.db import get_sync_engine, create_db_if_needed
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_if_needed()
    yield


app = FastAPI(
    title="Project Butler",
    description="Personal Health & Fitness Tracking API",
    version="0.2.0",
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
