#!/usr/bin/env python3
"""
Meetings Management Application
============================

Edge application for meetings management with API Gateway integration.
Communicates with Core AXLerate service through API Gateway.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import requests

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8001")
API_KEY = os.getenv("API_KEY", "meetings-app-key-456")
AXLERATE_BASE_URL = os.getenv("AXLERATE_BASE_URL", "http://10.X.X.X:8002")
AXLERATE_API_KEY = os.getenv("AXLERATE_API_KEY", "default-api-key")
CALENDAR_API_URL = os.getenv("CALENDAR_API_URL", "https://calendar.company.com/api")
CALENDAR_API_KEY = os.getenv("CALENDAR_API_KEY", "default-calendar-key")

# =============================================================================
# FastAPI Application
# =============================================================================
app = FastAPI(
    title="Meetings Management App",
    description="Edge application for meetings management",
    version="1.0.0"
)

# Security
security = HTTPBearer(auto_error=False)

# =============================================================================
# Pydantic Models
# =============================================================================
class MeetingRoom(BaseModel):
    """Meeting room model."""
    name: str
    extension: str
    capacity: int
    status: str = "available"
    location: Optional[str] = None
    equipment: List[str] = []

class Meeting(BaseModel):
    """Meeting model."""
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    room_name: str
    organizer: str
    participants: List[str] = []
    status: str = "scheduled"
    meeting_url: Optional[str] = None
    recording_enabled: bool = False

class CalendarEvent(BaseModel):
    """Calendar event model."""
    event_id: str
    title: str
    start_time: datetime
    end_time: datetime
    attendees: List[str] = []
    location: str
    description: str

class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Any = None
    error: Optional[str] = None

# =============================================================================
# Authentication
# =============================================================================
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key for authentication."""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# =============================================================================
# API Gateway Communication
# =============================================================================
async def call_api_gateway(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make authenticated call to API Gateway."""
    try:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        url = f"{API_GATEWAY_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"API Gateway call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with API Gateway: {str(e)}"
        )

# =============================================================================
# Calendar Integration
# =============================================================================
async def sync_with_calendar(meeting: Meeting) -> Optional[CalendarEvent]:
    """Sync meeting with external calendar system."""
    try:
        headers = {
            "Authorization": f"Bearer {CALENDAR_API_KEY}",
            "Content-Type": "application/json"
        }
        
        event_data = {
            "title": meeting.title,
            "description": meeting.description,
            "start_time": meeting.start_time.isoformat(),
            "end_time": meeting.end_time.isoformat(),
            "attendees": meeting.participants,
            "location": meeting.room_name
        }
        
        response = requests.post(
            f"{CALENDAR_API_URL}/events",
            headers=headers,
            json=event_data,
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        return CalendarEvent(
            event_id=result.get("event_id", ""),
            title=meeting.title,
            start_time=meeting.start_time,
            end_time=meeting.end_time,
            attendees=meeting.participants,
            location=meeting.room_name,
            description=meeting.description
        )
        
    except requests.RequestException as e:
        logger.error(f"Calendar sync failed: {e}")
        return None

# =============================================================================
# Health Check
# =============================================================================
@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint."""
    return APIResponse(
        message="Meetings Management App is healthy",
        data={"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    )

# =============================================================================
# Meeting Room Management Endpoints
# =============================================================================
@app.get("/rooms", response_model=APIResponse)
async def get_meeting_rooms(api_key: str = Depends(verify_api_key)):
    """Get all meeting rooms."""
    try:
        result = await call_api_gateway("/api/telephony/meeting-rooms")
        return APIResponse(
            data=result.get("data", []),
            message="Meeting rooms retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get meeting rooms: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to retrieve meeting rooms"
        )

@app.post("/rooms", response_model=APIResponse)
async def create_meeting_room(room: MeetingRoom, api_key: str = Depends(verify_api_key)):
    """Create a new meeting room."""
    try:
        result = await call_api_gateway(
            "/api/telephony/meeting-rooms",
            method="POST",
            data=room.dict()
        )
        return APIResponse(
            data=result.get("data", {}),
            message="Meeting room created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create meeting room: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to create meeting room"
        )

# =============================================================================
# Meeting Management Endpoints
# =============================================================================
@app.get("/meetings", response_model=APIResponse)
async def get_meetings(
    date: Optional[str] = None,
    status: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get meetings with optional filtering."""
    try:
        params = {}
        if date:
            params["date"] = date
        if status:
            params["status"] = status
            
        result = await call_api_gateway(
            "/api/census/meetings",
            method="GET",
            data=params
        )
        return APIResponse(
            data=result.get("data", []),
            message="Meetings retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get meetings: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to retrieve meetings"
        )

@app.post("/meetings", response_model=APIResponse)
async def create_meeting(meeting: Meeting, api_key: str = Depends(verify_api_key)):
    """Create a new meeting."""
    try:
        # Create meeting through API Gateway
        result = await call_api_gateway(
            "/api/census/meetings",
            method="POST",
            data=meeting.dict()
        )
        
        # Sync with calendar
        calendar_event = await sync_with_calendar(meeting)
        
        response_data = {
            "meeting": result.get("data", {}),
            "calendar_event": calendar_event.dict() if calendar_event else None
        }
        
        return APIResponse(
            data=response_data,
            message="Meeting created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to create meeting"
        )

@app.put("/meetings/{meeting_id}", response_model=APIResponse)
async def update_meeting(
    meeting_id: str, 
    meeting: Meeting, 
    api_key: str = Depends(verify_api_key)
):
    """Update a meeting."""
    try:
        result = await call_api_gateway(
            f"/api/census/meetings/{meeting_id}",
            method="PUT",
            data=meeting.dict()
        )
        
        # Sync with calendar
        calendar_event = await sync_with_calendar(meeting)
        
        response_data = {
            "meeting": result.get("data", {}),
            "calendar_event": calendar_event.dict() if calendar_event else None
        }
        
        return APIResponse(
            data=response_data,
            message="Meeting updated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to update meeting: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to update meeting"
        )

@app.delete("/meetings/{meeting_id}", response_model=APIResponse)
async def delete_meeting(meeting_id: str, api_key: str = Depends(verify_api_key)):
    """Delete a meeting."""
    try:
        result = await call_api_gateway(
            f"/api/census/meetings/{meeting_id}",
            method="DELETE"
        )
        
        # Delete from calendar
        try:
            headers = {
                "Authorization": f"Bearer {CALENDAR_API_KEY}",
                "Content-Type": "application/json"
            }
            
            requests.delete(
                f"{CALENDAR_API_URL}/events/{meeting_id}",
                headers=headers,
                timeout=10
            )
        except:
            pass  # Calendar deletion is optional
        
        return APIResponse(
            data=result.get("data", {}),
            message="Meeting deleted successfully"
        )
    except Exception as e:
        logger.error(f"Failed to delete meeting: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to delete meeting"
        )

# =============================================================================
# Meeting Analytics Endpoints
# =============================================================================
@app.get("/analytics/room-usage", response_model=APIResponse)
async def get_room_usage_analytics(
    start_date: str,
    end_date: str,
    api_key: str = Depends(verify_api_key)
):
    """Get room usage analytics."""
    try:
        result = await call_api_gateway(
            "/api/census/analytics/room-usage",
            method="GET",
            data={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        return APIResponse(
            data=result.get("data", {}),
            message="Room usage analytics retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get room usage analytics: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to retrieve room usage analytics"
        )

# =============================================================================
# Application Startup
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Meetings Management App starting up...")
    logger.info(f"API Gateway URL: {API_GATEWAY_URL}")
    logger.info(f"AXLERATE Base URL: {AXLERATE_BASE_URL}")
    logger.info(f"Calendar API URL: {CALENDAR_API_URL}")
    logger.info("Application ready to serve requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Meetings Management App shutting down...")

# =============================================================================
# Main Application Entry Point
# =============================================================================
if __name__ == "__main__":
    # Configure uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True,
        reload=False  # Set to True for development
    )
