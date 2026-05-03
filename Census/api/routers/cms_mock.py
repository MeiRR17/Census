"""
CMS Meetings API Router
ניהול ועידות CMS מדומות
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional, Any

from services.cms_meetings import cms_meetings_service

logger = logging.getLogger(__name__)

# Create FastAPI router
cms_meetings_router = APIRouter(
    prefix="/api/v1/cms/meetings",
    tags=["CMS Mock"],
    responses={404: {"description": "Not found"}}
)

@cms_meetings_router.get("/all_meetings", response_model=List[Dict[str, Any]])
async def get_all_meetings():
    """
    Get all CMS meetings
    
    Returns:
        List of all CMS meetings
    """
    try:
        meetings = await cms_meetings_service.get_meetings()
        return meetings
    except Exception as e:
        logger.error(f"Failed to get all CMS meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/", response_model=List[Dict[str, Any]])
async def get_meetings(
    type: Optional[str] = Query(None, description="Filter by meeting type (audio/video/blast_dial)")
):
    """
    Get all CMS meetings, optionally filtered by type
    
    Args:
        type: Optional meeting type filter
        
    Returns:
        List of CMS meetings
    """
    try:
        meetings = await cms_meetings_service.get_meetings(meeting_type=type)
        return meetings
    except Exception as e:
        logger.error(f"Failed to get CMS meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/stats", response_model=Dict[str, Any])
async def get_meeting_stats():
    """
    Get CMS meetings statistics
    
    Returns:
        Meeting statistics
    """
    try:
        stats = cms_meetings_service.get_meeting_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get meeting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/number/{number}", response_model=Dict[str, Any])
async def get_meeting_by_number(number: str):
    """
    Get a specific CMS meeting by number
    
    Args:
        number: Meeting number
        
    Returns:
        Meeting details
    """
    try:
        meeting = await cms_meetings_service.get_meeting_by_id(number)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting by number {number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/group/{group_uuid}", response_model=List[Dict[str, Any]])
async def get_meetings_by_group(group_uuid: str):
    """
    Get CMS meetings by group UUID
    
    Args:
        group_uuid: Group UUID
        
    Returns:
        List of meetings in the group
    """
    try:
        meetings = await cms_meetings_service.get_meetings()
        filtered = [m for m in meetings if m.get("group") == group_uuid]
        return filtered
    except Exception as e:
        logger.error(f"Failed to get meetings by group {group_uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/{meeting_uuid}", response_model=Dict[str, Any])
async def get_meeting_by_uuid(meeting_uuid: str):
    """
    Get a specific CMS meeting by UUID
    
    Args:
        meeting_uuid: Meeting UUID
        
    Returns:
        Meeting details
    """
    try:
        meeting = await cms_meetings_service.get_meeting_by_id(meeting_uuid)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting {meeting_uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.post("/create_meeting", response_model=Dict[str, Any])
async def create_meeting_by_access_level(meeting_data: Dict[str, Any]):
    """
    Create a new CMS meeting by access level
    
    Args:
        meeting_data: Meeting data with access level
        
    Returns:
        Created meeting details
    """
    try:
        meeting = await cms_meetings_service.create_meeting(meeting_data)
        if not meeting:
            raise HTTPException(status_code=400, detail="Invalid meeting data")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create meeting by access level: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.post("/", response_model=Dict[str, Any])
async def create_meeting(meeting_data: Dict[str, Any]):
    """
    Create a new CMS meeting
    
    Args:
        meeting_data: Meeting data
        
    Returns:
        Created meeting details
    """
    try:
        meeting = await cms_meetings_service.create_meeting(meeting_data)
        if not meeting:
            raise HTTPException(status_code=400, detail="Invalid meeting data")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.put("/{meeting_uuid}", response_model=Dict[str, Any])
async def update_meeting_by_uuid(
    meeting_uuid: str,
    meeting_data: Dict[str, Any]
):
    """
    Update a CMS meeting by UUID
    
    Args:
        meeting_uuid: Meeting UUID
        meeting_data: Updated meeting data
        
    Returns:
        Updated meeting details
    """
    try:
        meeting = await cms_meetings_service.get_meeting_by_id(meeting_uuid)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        # Update meeting fields
        for key, value in meeting_data.items():
            if key in meeting:
                meeting[key] = value
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update meeting {meeting_uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.put("/password/{meeting_uuid}", response_model=Dict[str, Any])
async def update_meeting_password_by_uuid(
    meeting_uuid: str,
    password_data: Dict[str, str]
):
    """
    Update meeting password by UUID
    
    Args:
        meeting_uuid: Meeting UUID
        password_data: New password data
        
    Returns:
        Updated meeting details
    """
    try:
        new_password = password_data.get("password", "")
        meeting = await cms_meetings_service.update_meeting_password(meeting_uuid, new_password)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update meeting password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.put("/{meeting_id}/password", response_model=Dict[str, Any])
async def update_meeting_password(
    meeting_id: str,
    password_data: Dict[str, str]
):
    """
    Update meeting password
    
    Args:
        meeting_id: Meeting ID
        password_data: New password data
        
    Returns:
        Updated meeting details
    """
    try:
        new_password = password_data.get("password", "")
        meeting = await cms_meetings_service.update_meeting_password(meeting_id, new_password)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update meeting password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.put("/number/{meeting_number}", response_model=Dict[str, Any])
async def update_meeting_by_number(
    meeting_number: str,
    meeting_data: Dict[str, Any]
):
    """
    Update a CMS meeting by number
    
    Args:
        meeting_number: Meeting number
        meeting_data: Updated meeting data
        
    Returns:
        Updated meeting details
    """
    try:
        meeting = await cms_meetings_service.get_meeting_by_id(meeting_number)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        # Update meeting fields
        for key, value in meeting_data.items():
            if key in meeting:
                meeting[key] = value
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update meeting by number {meeting_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.delete("/{meeting_uuid}", response_model=Dict[str, Any])
async def delete_meeting_by_uuid(
    meeting_uuid: str,
    actor: Optional[Dict[str, Any]] = None
):
    """
    Delete a CMS meeting by UUID
    
    Args:
        meeting_uuid: Meeting UUID
        actor: User performing the deletion
        
    Returns:
        Deletion result
    """
    try:
        result = await cms_meetings_service.delete_meeting(meeting_uuid, actor)
        return result
    except Exception as e:
        logger.error(f"Failed to delete meeting {meeting_uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.delete("/{meeting_id}", response_model=Dict[str, Any])
async def delete_meeting(
    meeting_id: str,
    actor: Optional[Dict[str, Any]] = None
):
    """
    Delete a CMS meeting
    
    Args:
        meeting_id: Meeting ID
        actor: User performing the deletion
        
    Returns:
        Deletion result
    """
    try:
        result = await cms_meetings_service.delete_meeting(meeting_id, actor)
        return result
    except Exception as e:
        logger.error(f"Failed to delete meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/types/list", response_model=List[str])
async def get_meeting_types():
    """
    Get available meeting types
    
    Returns:
        List of meeting types
    """
    return ["audio", "video", "blast_dial"]

@cms_meetings_router.get("/calls/active", response_model=List[Dict[str, Any]])
async def get_active_calls():
    """
    Get all active calls in CMS meetings
    
    Returns:
        List of active calls
    """
    try:
        meetings = await cms_meetings_service.get_meetings()
        active_calls = []
        for meeting in meetings:
            if meeting.get("status") == "active" and meeting.get("participants_count", 0) > 0:
                active_calls.append({
                    "call_id": meeting.get("id"),
                    "meeting_id": meeting.get("meeting_id"),
                    "name": meeting.get("name"),
                    "participants_count": meeting.get("participants_count"),
                    "duration": meeting.get("duration", 0),
                    "status": meeting.get("status"),
                    "cms_node": meeting.get("cms_node")
                })
        return active_calls
    except Exception as e:
        logger.error(f"Failed to get active calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cms_meetings_router.get("/status/list", response_model=List[str])
async def get_meeting_statuses():
    """
    Get available meeting statuses
    
    Returns:
        List of meeting statuses
    """
    return ["active", "idle", "scheduled", "not_in_use"]
