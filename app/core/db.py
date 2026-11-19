from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Session:
    sync_engine = create_engine(settings.sync_database_url)
    with Session(sync_engine) as session:
        yield session
