import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Text
from config import BASE_DIR

# DB paths
DB_PATH = BASE_DIR / "sessions.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Create an async engine with connection pooling parameters for SQLite.
# check_same_thread=False is needed for SQLite when using multithreading or async pool.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    connect_args={"check_same_thread": False}
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"
    session_id = Column(String, primary_key=True, index=True)
    history = Column(Text, nullable=False)
    updated_at = Column(String, nullable=True)

async def init_db():
    """Initializes the database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session():
    """Dependency provider for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        yield session
