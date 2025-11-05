from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi_ddd.core.config import settings


DATABASE_URL = (
    f"postgresql+asyncpg://{settings.database_user}:{settings.database_password}@"
    f"{settings.database_host}:{settings.database_port}/{settings.database_name}"
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)


# --- DB initialization ---
async def create_db_and_tables() -> None:
    """Create all tables asynchronously at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# --- Session dependency ---
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a new SQLModel AsyncSession for each request."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# --- Synchronous helper ---
def get_db_url() -> str:
    """Return synchronous DB URL (for Alembic migrations)."""
    return DATABASE_URL.replace("+asyncpg", "")


# --- FastAPI dependency alias ---
SessionDep = Annotated[AsyncSession, Depends(get_session)]
