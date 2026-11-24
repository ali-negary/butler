from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlmodel import Session as SQLModelSession
from app.core.config import get_settings

_settings = get_settings()

_engine = None
_sync_engine = None
_factory = None


def get_engine():
    global _engine, _factory
    if _engine is None:
        _engine = create_async_engine(_settings.database_url, echo=False)
        _factory = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _engine, _factory


def get_factory():
    return get_engine()[1]


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(_settings.sync_database_url, echo=False, pool_pre_ping=True)
    return _sync_engine


def create_db_if_needed():
    try:
        engine = get_sync_engine()
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Warning: could not create DB tables: {e}")


async def get_db() -> AsyncSession:
    eng, fac = get_engine()
    async with fac() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> SQLModelSession:
    se = get_sync_engine()
    with SQLModelSession(se) as session:
        yield session
