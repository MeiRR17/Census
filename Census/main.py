"""
CENSUS - Centralized Enterprise Network Communication Unified System
FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.config import get_settings, Settings
from database.session import init_db, get_db, close_db_connections
from api.routers.census import census_router
from api.routers.cms import cms_router
from api.routers.cms_meetings import cms_meetings_router
from api.routers.cucm_mock import cucm_mock_router
from api.routers.meetingplace_mock import meetingplace_mock_router
from api.routers.meetingplace import meetingplace_router
from core.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    
    # 1. Initialize database
    await init_db()
    print("Database initialized successfully")
    
    # 2. Start background scheduler
    start_scheduler()
    print("Background scheduler started")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    stop_scheduler()
    print("Scheduler stopped")
    await close_db_connections()
    print("Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Centralized Enterprise Network Communication Unified System - "
                "A unified inventory platform for communication endpoints.",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(census_router)
# app.include_router(cms_router)  # Temporarily disabled due to connection loop
app.include_router(cms_meetings_router)
app.include_router(cucm_mock_router)
app.include_router(meetingplace_mock_router)
app.include_router(meetingplace_router)


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns:
        dict: Status message and database connectivity status.
    """
    try:
        # Check database connectivity
        result = await db.execute(text("SELECT 1"))
        db_status = "connected" if result.scalar() == 1 else "error"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
