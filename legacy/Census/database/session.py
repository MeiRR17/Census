"""
Database session management for CENSUS.
Provides async SQLAlchemy engine, session factory, and FastAPI dependency.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.engine import make_url

from database.models import Base
from core.config import get_settings


settings = get_settings()

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database:
    1. Create all tables based on Base metadata
    2. Try to create pgvector extension if available
    
    This function uses a sync connection for initialization
    since CREATE EXTENSION requires a sync operation.
    """
    from sqlalchemy import create_engine
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Create sync engine for initialization
    sync_engine = create_engine(settings.DATABASE_URL_SYNC, future=True)
    
    with sync_engine.connect() as conn:
        # Create all tables first
        Base.metadata.create_all(conn)
        logger.info("Database tables created successfully")
        
        # Try to create pgvector extension (optional for MVP)
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("pgvector extension created successfully")
        except Exception as e:
            logger.warning(f"pgvector extension not available: {e}")
            logger.info("Continuing without pgvector extension...")
    
    # Note: Tables already created via sync engine above
    # No need to create them again with async engine
    


async def close_db_connections() -> None:
    """Close all database connections."""
    await async_engine.dispose()
