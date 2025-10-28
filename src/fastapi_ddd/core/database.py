from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Use asyncpg driver for async PostgreSQL connection
DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@"
    f"{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
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
    async with AsyncSession(engine) as session:
        yield session


# --- Optional helper ---
def get_db_url() -> str:
    return DATABASE_URL.replace("+asyncpg", "")


# --- FastAPI dependency alias ---
SessionDep = Annotated[AsyncSession, Depends(get_session)]
