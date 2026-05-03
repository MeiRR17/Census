"""
CMS API Router
Cisco Meeting Server API endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional, Any
from datetime import datetime

from database.session import get_db

logger = logging.getLogger(__name__)

# Create FastAPI router
cms_router = APIRouter(
    prefix="/api/v1/cms",
    tags=["CMS"],
    responses={404: {"description": "Not found"}}
)

@cms_router.get("/health", response_model=Dict[str, Any])
async def cms_health_check():
    """CMS health check endpoint"""
    try:
        # Skip actual CMS connection test to avoid loop
        # cms_client = CMS.create_from_env()
        # is_connected = cms_client.test_connection()
        
        return {
            "status": "ok",
            "service": "CMS",
            "connected": False,  # Mock - not actually connected
            "cms_url": "http://localhost:8000",
            "message": "Mock CMS service - no actual connection",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"CMS health check failed: {e}")
        return {
            "status": "error",
            "service": "CMS",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

@cms_router.get("/cospaces", response_model=List[Dict[str, Any]])
async def list_cospaces():
    """
    List all CoSpaces (meeting rooms)
    
    Returns:
        List of CoSpace objects
    """
    try:
        # Return mock data to avoid connection loop
        return [
            {
                "id": "cospace-1",
                "name": "Main Conference Room",
                "uri": "main-room",
                "passcode": "123456",
                "status": "active"
            },
            {
                "id": "cospace-2", 
                "name": "Training Room",
                "uri": "training-room",
                "passcode": "789012",
                "status": "idle"
            }
        ]
    except Exception as e:
        logger.error(f"Failed to list CoSpaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.post("/cospaces", response_model=Dict[str, Any])
async def create_cospace(
    name: str,
    uri: Optional[str] = None,
    passcode: Optional[str] = None
):
    """
    Create a new CoSpace
    
    Args:
        name: CoSpace name
        uri: Optional URI for the CoSpace
        passcode: Optional passcode for access
        
    Returns:
        Created CoSpace details
    """
    try:
        # Return mock data to avoid connection loop
        return {
            "id": f"cospace-{hash(name) % 10000}",
            "name": name,
            "uri": uri or name.lower().replace(" ", "-"),
            "passcode": passcode or "123456",
            "status": "created"
        }
    except Exception as e:
        logger.error(f"Failed to create CoSpace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.delete("/cospaces/{cospace_id}")
async def delete_cospace(cospace_id: str):
    """
    Delete a CoSpace
    
    Args:
        cospace_id: ID of CoSpace to delete
        
    Returns:
        Success status
    """
    try:
        # Return mock data to avoid connection loop
        return {"success": True, "cospace_id": cospace_id}
    except Exception as e:
        logger.error(f"Failed to delete CoSpace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/calls", response_model=List[Dict[str, Any]])
async def get_active_calls():
    """
    Get all active calls
    
    Returns:
        List of active call objects
    """
    try:
        # Return mock data to avoid connection loop
        return [
            {
                "call_id": "call-001",
                "participants": 5,
                "duration": 120,
                "status": "active",
                "cospace_id": "cospace-1"
            },
            {
                "call_id": "call-002",
                "participants": 3,
                "duration": 45,
                "status": "active",
                "cospace_id": "cospace-2"
            }
        ]
    except Exception as e:
        logger.error(f"Failed to get active calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/calls/{call_id}", response_model=Dict[str, Any])
async def get_call_details(call_id: str):
    """
    Get call details
    
    Args:
        call_id: ID of the call
        
    Returns:
        Call details
    """
    try:
        # Return mock data to avoid connection loop
        return {
            "call_id": call_id,
            "participants": 5,
            "duration": 120,
            "status": "active",
            "cospace_id": "cospace-1",
            "start_time": "2026-04-30T12:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get call details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/calls/{call_id}/participants", response_model=List[Dict[str, Any]])
async def get_call_participants(call_id: str):
    """
    Get call participants
    
    Args:
        call_id: ID of the call
        
    Returns:
        List of participant objects
    """
    try:
        # Return mock data to avoid connection loop
        return [
            {
                "name": "User 1",
                "leg_id": "leg-001",
                "muted": False,
                "joined_at": "2026-04-30T12:00:00Z"
            },
            {
                "name": "User 2",
                "leg_id": "leg-002",
                "muted": True,
                "joined_at": "2026-04-30T12:01:00Z"
            }
        ]
    except Exception as e:
        logger.error(f"Failed to get call participants: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.put("/calls/{call_id}/participants/{participant_name}/mute")
async def mute_participant(
    call_id: str,
    participant_name: str,
    mute: bool = True
):
    """
    Mute or unmute a participant
    
    Args:
        call_id: ID of the call
        participant_name: Name of the participant
        mute: True to mute, False to unmute
        
    Returns:
        Success status
    """
    try:
        # Return mock data to avoid connection loop
        return {
            "success": True,
            "call_id": call_id,
            "participant": participant_name,
            "muted": mute
        }
    except Exception as e:
        logger.error(f"Failed to mute participant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.delete("/calls/{call_id}/participants/{participant_name}")
async def kick_participant(
    call_id: str,
    participant_name: str
):
    """
    Kick a participant from call
    
    Args:
        call_id: ID of the call
        participant_name: Name of the participant to kick
        
    Returns:
        Success status
    """
    try:
        # Return mock data to avoid connection loop
        return {
            "success": True,
            "call_id": call_id,
            "participant": participant_name,
            "kicked": True
        }
    except Exception as e:
        logger.error(f"Failed to kick participant: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_router.get("/system/info", response_model=Dict[str, Any])
async def get_system_info():
    """
    Get CMS system information
    
    Returns:
        System information
    """
    try:
        # Return mock data to avoid connection loop
        return {
            "version": "1.0.0",
            "status": "operational",
            "hostname": "cms-mock-server",
            "uptime": 86400,
            "active_calls": 2,
            "total_cospaces": 10
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
