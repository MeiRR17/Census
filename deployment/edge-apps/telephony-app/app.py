#!/usr/bin/env python3
"""
Telephony Management Application
============================

Edge application for telephony management with API Gateway integration.
Communicates with Core AXLerate service through API Gateway.
"""

import os
import asyncio
import logging
from datetime import datetime
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
API_KEY = os.getenv("API_KEY", "telephony-app-key-123")
AXLERATE_BASE_URL = os.getenv("AXLERATE_BASE_URL", "http://10.X.X.X:8002")
AXLERATE_API_KEY = os.getenv("AXLERATE_API_KEY", "default-api-key")

# =============================================================================
# FastAPI Application
# =============================================================================
app = FastAPI(
    title="Telephony Management App",
    description="Edge application for telephony management",
    version="1.0.0"
)

# Security
security = HTTPBearer(auto_error=False)

# =============================================================================
# Pydantic Models
# =============================================================================
class TelephonyDevice(BaseModel):
    """Telephony device model."""
    device_name: str
    mac_address: str
    device_type: str
    status: str
    user_id: Optional[str] = None
    location: Optional[str] = None

class MeetingRoom(BaseModel):
    """Meeting room model."""
    name: str
    extension: str
    capacity: int
    status: str = "available"

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
# Health Check
# =============================================================================
@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint."""
    return APIResponse(
        message="Telephony Management App is healthy",
        data={"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    )

# =============================================================================
# Device Management Endpoints
# =============================================================================
@app.get("/devices", response_model=APIResponse)
async def get_devices(api_key: str = Depends(verify_api_key)):
    """Get all telephony devices."""
    try:
        result = await call_api_gateway("/api/census/devices")
        return APIResponse(
            data=result.get("data", []),
            message="Devices retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Failed to get devices: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to retrieve devices"
        )

@app.post("/devices", response_model=APIResponse)
async def create_device(device: TelephonyDevice, api_key: str = Depends(verify_api_key)):
    """Create a new telephony device."""
    try:
        result = await call_api_gateway(
            "/api/telephony/devices",
            method="POST",
            data=device.dict()
        )
        return APIResponse(
            data=result.get("data", {}),
            message="Device created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create device: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to create device"
        )

@app.put("/devices/{device_id}", response_model=APIResponse)
async def update_device(device_id: str, device: TelephonyDevice, api_key: str = Depends(verify_api_key)):
    """Update a telephony device."""
    try:
        result = await call_api_gateway(
            f"/api/telephony/devices/{device_id}",
            method="PUT",
            data=device.dict()
        )
        return APIResponse(
            data=result.get("data", {}),
            message="Device updated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to update device: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to update device"
        )

@app.delete("/devices/{device_id}", response_model=APIResponse)
async def delete_device(device_id: str, api_key: str = Depends(verify_api_key)):
    """Delete a telephony device."""
    try:
        result = await call_api_gateway(
            f"/api/telephony/devices/{device_id}",
            method="DELETE"
        )
        return APIResponse(
            data=result.get("data", {}),
            message="Device deleted successfully"
        )
    except Exception as e:
        logger.error(f"Failed to delete device: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            message="Failed to delete device"
        )

# =============================================================================
# Meeting Room Management Endpoints
# =============================================================================
@app.get("/meeting-rooms", response_model=APIResponse)
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

@app.post("/meeting-rooms", response_model=APIResponse)
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
# Direct AXLerate Communication (Fallback)
# =============================================================================
async def call_axlerate_direct(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Direct call to AXLerate service (fallback)."""
    try:
        headers = {
            "Authorization": f"Bearer {AXLERATE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{AXLERATE_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Direct AXLerate call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with AXLerate: {str(e)}"
        )

# =============================================================================
# Application Startup
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Telephony Management App starting up...")
    logger.info(f"API Gateway URL: {API_GATEWAY_URL}")
    logger.info(f"AXLERATE Base URL: {AXLERATE_BASE_URL}")
    logger.info("Application ready to serve requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Telephony Management App shutting down...")

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
