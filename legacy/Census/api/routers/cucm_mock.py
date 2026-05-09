"""
CUCM Mock API Router
ניהול נתוני CUCM מדומים
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional, Any

from services.cucm_mock import cucm_mock_service
from schemas.census import CUCMPhoneCreateRequest

logger = logging.getLogger(__name__)

# Create FastAPI router
cucm_mock_router = APIRouter(
    prefix="/api/v1/cucm/mock",
    tags=["CUCM Mock"],
    responses={404: {"description": "Not found"}}
)

@cucm_mock_router.get("/stats", response_model=Dict[str, Any])
async def get_cucm_stats():
    """
    Get CUCM mock statistics
    
    Returns:
        CUCM statistics
    """
    try:
        stats = cucm_mock_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get CUCM stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.get("/phones", response_model=List[Dict[str, Any]])
async def get_phones(status: Optional[str] = None):
    """
    Get all CUCM phones, optionally filtered by status
    
    Args:
        status: Optional status filter (registered, unregistered, rejected)
        
    Returns:
        List of phones
    """
    try:
        phones = await cucm_mock_service.get_phones(status=status)
        return phones
    except Exception as e:
        logger.error(f"Failed to get phones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.get("/phones/{phone_id}", response_model=Dict[str, Any])
async def get_phone_by_id(phone_id: str):
    """
    Get phone by ID
    
    Args:
        phone_id: Phone ID
        
    Returns:
        Phone details
    """
    try:
        phone = await cucm_mock_service.get_phone_by_id(phone_id)
        if not phone:
            raise HTTPException(status_code=404, detail="Phone not found")
        return phone
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get phone {phone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.post("/phones", response_model=Dict[str, Any])
async def create_phone(phone_data: CUCMPhoneCreateRequest):
    """
    Create a new phone with all possible fields.
    
    Required field:
    - mac_address: MAC address (e.g., "00:11:22:33:44:55")
    
    Optional fields:
    - description: Phone description (default: "New Phone")
    - model: Phone model (default: "Cisco 7841")
    - ip_address: IP address (default: "10.1.1.200")
    - device_pool: Device pool name (default: "Default")
    - calling_search_space: CSS (default: "CSS-Internal")
    - line_dn: Directory Number (default: "")
    - line_partition: Line partition (default: "PT-Internal")
    - status: Phone status (default: "unregistered")
    
    Args:
        phone_data: Phone creation data
        
    Returns:
        Created phone details
    
    Example:
        {
            "mac_address": "00:11:22:33:44:99",
            "description": "New Office Phone",
            "model": "Cisco 8851",
            "ip_address": "10.1.1.150",
            "device_pool": "Sales-Pool",
            "calling_search_space": "CSS-Sales",
            "line_dn": "2500",
            "line_partition": "PT-Sales",
            "status": "registered"
        }
    """
    try:
        phone = await cucm_mock_service.create_phone(phone_data.model_dump())
        if not phone:
            raise HTTPException(status_code=400, detail="Invalid phone data")
        return phone
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create phone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.delete("/phones/{phone_id}")
async def delete_phone(phone_id: str):
    """
    Delete a phone
    
    Args:
        phone_id: Phone ID
        
    Returns:
        Deletion result
    """
    try:
        result = await cucm_mock_service.delete_phone(phone_id)
        if not result["deleted"]:
            raise HTTPException(status_code=404, detail="Phone not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete phone {phone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(department: Optional[str] = None):
    """
    Get all CUCM users, optionally filtered by department
    
    Args:
        department: Optional department filter
        
    Returns:
        List of users
    """
    try:
        users = await cucm_mock_service.get_users(department=department)
        return users
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(user_id: str):
    """
    Get user by ID
    
    Args:
        user_id: User ID
        
    Returns:
        User details
    """
    try:
        user = await cucm_mock_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.get("/lines", response_model=List[Dict[str, Any]])
async def get_lines(partition: Optional[str] = None):
    """
    Get all CUCM lines, optionally filtered by partition
    
    Args:
        partition: Optional partition filter
        
    Returns:
        List of lines
    """
    try:
        lines = await cucm_mock_service.get_lines(partition=partition)
        return lines
    except Exception as e:
        logger.error(f"Failed to get lines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@cucm_mock_router.get("/lines/{pattern}", response_model=Dict[str, Any])
async def get_line_by_pattern(pattern: str):
    """
    Get line by pattern
    
    Args:
        pattern: Line pattern
        
    Returns:
        Line details
    """
    try:
        line = await cucm_mock_service.get_line_by_pattern(pattern)
        if not line:
            raise HTTPException(status_code=404, detail="Line not found")
        return line
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get line {pattern}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
