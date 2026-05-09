"""
MeetingPlace API Router - Real Server Integration
ניהול MeetingPlace עם חיבור אמיתי לשרת
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any

from api.routers.meetingplace_mock import (
    MeetingPlaceMeetingCreate, 
    MeetingPlaceUserCreate,
    meetingplace_mock_service
)

# Real MeetingPlace service (requires proper SDK installation in container)
# To use real server, uncomment below and set USE_MOCK = False
# from services.meetingplace_service import meetingplace_service

logger = logging.getLogger(__name__)

# Create FastAPI router
meetingplace_router = APIRouter(
    prefix="/api/v1/meetingplace",
    tags=["MeetingPlace"],
    responses={404: {"description": "Not found"}}
)

# ==========================================
# Configuration: Use Mock or Real Server
# ==========================================
# NOTE: Currently using MOCK only. To use real server:
# 1. Ensure ciscoaxl SDK is properly installed in container
# 2. Create meeting_place_config.ini with server details
# 3. Uncomment the import above
# 4. Set USE_MOCK = False
USE_MOCK = True

# Use mock service (for real server, see instructions above)
service = meetingplace_mock_service
logger.info("Using MeetingPlace MOCK service")


# ==========================================
# API Endpoints
# ==========================================

@meetingplace_router.get("/stats", response_model=Dict[str, Any])
async def get_meetingplace_stats():
    """Get MeetingPlace statistics"""
    try:
        stats = service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get MeetingPlace stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.get("/meetings", response_model=List[Dict[str, Any]])
async def get_meetings(status: Optional[str] = None):
    """Get all meetings"""
    try:
        meetings = await service.get_meetings(status=status)
        return meetings
    except Exception as e:
        logger.error(f"Failed to get meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.get("/meetings/{meeting_id}", response_model=Dict[str, Any])
async def get_meeting_by_id(meeting_id: str):
    """Get meeting by ID"""
    try:
        meeting = await service.get_meeting_by_id(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.post("/meetings", response_model=Dict[str, Any])
async def create_meeting(meeting_data: MeetingPlaceMeetingCreate):
    """Create a new meeting"""
    try:
        meeting = await service.create_meeting(meeting_data.model_dump())
        if not meeting:
            raise HTTPException(status_code=400, detail="Failed to create meeting")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.post("/meetings/{meeting_id}/end", response_model=Dict[str, Any])
async def end_meeting(meeting_id: str):
    """End an active meeting"""
    try:
        meeting = await service.end_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete a meeting"""
    try:
        result = await service.delete_meeting(meeting_id)
        if not result.get("deleted"):
            raise HTTPException(status_code=404, detail="Meeting not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(department: Optional[str] = None):
    """Get all users"""
    try:
        users = await service.get_users(department=department)
        return users
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(user_id: str):
    """Get user by ID"""
    try:
        user = await service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.post("/users", response_model=Dict[str, Any])
async def create_user(user_data: MeetingPlaceUserCreate):
    """Create a new user"""
    try:
        user = await service.create_user(user_data.model_dump())
        if not user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@meetingplace_router.get("/connection/status")
async def get_connection_status():
    """Check MeetingPlace connection status"""
    if USE_MOCK:
        return {
            "mode": "MOCK",
            "connected": True,
            "message": "Using mock data - no real server connection"
        }
    else:
        is_connected = meetingplace_service.is_connected()
        return {
            "mode": "REAL",
            "connected": is_connected,
            "message": "Connected to real MeetingPlace server" if is_connected else "Failed to connect to MeetingPlace server"
        }
