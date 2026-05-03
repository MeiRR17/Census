"""
CUCM Mock API Router
ניהול נתוני CUCM מדומים
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional, Any

from services.cucm_mock import cucm_mock_service

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
async def create_phone(phone_data: Dict[str, Any]):
    """
    Create a new phone
    
    Args:
        phone_data: Phone data
        
    Returns:
        Created phone details
    """
    try:
        phone = await cucm_mock_service.create_phone(phone_data)
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
