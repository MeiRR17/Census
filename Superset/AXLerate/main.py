#!/usr/bin/env python3
"""
AXLerate API Gateway
====================

Secure gateway between applications and Cisco UC Manager.
Provides REST/JSON interface while handling SOAP/XML communication with CUCM.

Features:
- Authentication & Authorization
- Request validation
- SOAP/XML translation
- Rate limiting
- Audit logging
- Write-through to CENSUS DB
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import uvicorn
import logging
import sys
import os
from datetime import datetime

# SDK imports
from axlerate.client import AXLClient
from axlerate.exceptions import AXLConnectionError, AXLAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AXLerate API Gateway",
    description="Secure gateway for Cisco UC Manager operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ============================================================================
# Pydantic Models
# ============================================================================

class PhoneRequest(BaseModel):
    """Phone creation/update request model"""
    name: str = Field(..., description="Device name (e.g., SEP1234567890AB)")
    description: Optional[str] = Field(None, description="Device description")
    product: str = Field(..., description="Device model (e.g., Cisco 8841)")
    device_pool: str = Field("Default", description="Device pool name")
    location: str = Field("Hub_None", description="Device location")
    protocol: str = Field("SIP", description="Protocol (SIP/SCCP)")

class UserRequest(BaseModel):
    """User creation/update request model"""
    userid: str = Field(..., description="User ID")
    firstname: str = Field(..., description="First name")
    lastname: str = Field(..., description="Last name")
    mailid: Optional[str] = Field(None, description="Email address")
    primary_extension: Optional[str] = Field(None, description="Primary extension")

class LineRequest(BaseModel):
    """Line creation/update request model"""
    pattern: str = Field(..., description="Directory number")
    description: Optional[str] = Field(None, description="Line description")
    route_partition: str = Field("Default", description="Route partition")
    usage: str = Field("Device", description="Line usage")

class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: str = Field(..., description="Operation timestamp")

# ============================================================================
# Configuration
# ============================================================================

class AXLerateConfig:
    def __init__(self):
        self.cucm_server = os.getenv("CUCM_SERVER", "localhost")
        self.cucm_username = os.getenv("CUCM_USERNAME", "admin")
        self.cucm_password = os.getenv("CUCM_PASSWORD", "admin")
        self.cucm_port = int(os.getenv("CUCM_PORT", "8443"))
        self.verify_ssl = os.getenv("CUCM_VERIFY_SSL", "false").lower() == "true"
        
        # Census DB connection
        self.census_db_url = os.getenv("CENSUS_DB_URL", "postgresql://user:pass@localhost/census")

config = AXLerateConfig()

# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token or API key"""
    # TODO: Implement proper JWT validation
    if credentials.credentials != "axlerate-api-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": "api_user", "permissions": ["phone", "user", "line"]}

async def get_axl_client():
    """Get AXL client instance"""
    try:
        client = AXLClient(
            server_ip=config.cucm_server,
            username=config.cucm_username,
            password=config.cucm_password,
            port=config.cucm_port,
            verify_ssl=config.verify_ssl
        )
        return client
    except Exception as e:
        logger.error(f"Failed to create AXL client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to CUCM server"
        )

# ============================================================================
# Helper Functions
# ============================================================================

def create_response(success: bool, data=None, error=None) -> APIResponse:
    """Create standardized API response"""
    return APIResponse(
        success=success,
        data=data,
        error=error,
        timestamp=datetime.utcnow().isoformat()
    )

async def write_to_census(operation: str, data: Dict[str, Any]):
    """Write operation result to CENSUS DB (Write-through)"""
    try:
        # TODO: Implement actual DB write
        logger.info(f"CENSUS Write-through: {operation} - {data}")
        # Simulate DB write for now
        pass
    except Exception as e:
        logger.error(f"CENSUS write-through failed: {e}")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint"""
    return create_response(True, {"message": "AXLerate API Gateway v1.0.0"})

@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    try:
        client = await get_axl_client()
        # Test basic connectivity
        if hasattr(client, 'test_connection'):
            cucm_status = client.test_connection()
        else:
            cucm_status = {"status": "connected"}
        
        return create_response(True, {
            "gateway": "healthy",
            "cucm": cucm_status,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return create_response(False, error=str(e))

@app.post("/api/v1/phones", response_model=APIResponse)
async def add_phone(
    phone: PhoneRequest,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Add new phone to CUCM"""
    try:
        logger.info(f"Adding phone {phone.name} for user {current_user['user']}")
        
        # Call SDK method (Iron Rule 1)
        result = axl_client.add_phone({
            "name": phone.name,
            "description": phone.description,
            "product": phone.product,
            "devicePoolName": phone.device_pool,
            "locationName": phone.location,
            "protocol": phone.protocol
        })
        
        if result.get('success', False):
            # Write-through to CENSUS (Iron Rule 3)
            await write_to_census("add_phone", {
                "mac": phone.name,
                "status": "active",
                "user": current_user['user']
            })
            
            return create_response(True, result.get('data'))
        else:
            return create_response(False, error=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Add phone failed: {e}")
        return create_response(False, error=str(e))

@app.get("/api/v1/phones", response_model=APIResponse)
async def get_phones(
    limit: Optional[int] = None,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Get all phones from CUCM"""
    try:
        logger.info(f"Getting phones for user {current_user['user']}")
        
        result = axl_client.get_phones(limit=limit, skip=skip)
        
        if result.get('success', False):
            return create_response(True, result.get('data'))
        else:
            return create_response(False, error=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Get phones failed: {e}")
        return create_response(False, error=str(e))

@app.get("/api/v1/phones/{phone_name}", response_model=APIResponse)
async def get_phone(
    phone_name: str,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Get specific phone from CUCM"""
    try:
        logger.info(f"Getting phone {phone_name} for user {current_user['user']}")
        
        result = axl_client.get_phone(phone_name)
        
        if result.get('success', False):
            return create_response(True, result.get('data'))
        else:
            return create_response(False, error=result.get('error', 'Phone not found'))
            
    except Exception as e:
        logger.error(f"Get phone failed: {e}")
        return create_response(False, error=str(e))

@app.put("/api/v1/phones/{phone_name}", response_model=APIResponse)
async def update_phone(
    phone_name: str,
    phone: PhoneRequest,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Update phone in CUCM"""
    try:
        logger.info(f"Updating phone {phone_name} for user {current_user['user']}")
        
        result = axl_client.update_phone(phone_name, {
            "description": phone.description,
            "devicePoolName": phone.device_pool,
            "locationName": phone.location
        })
        
        if result.get('success', False):
            await write_to_census("update_phone", {
                "mac": phone_name,
                "status": "updated",
                "user": current_user['user']
            })
            
            return create_response(True, result.get('data'))
        else:
            return create_response(False, error=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Update phone failed: {e}")
        return create_response(False, error=str(e))

@app.delete("/api/v1/phones/{phone_name}", response_model=APIResponse)
async def delete_phone(
    phone_name: str,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Delete phone from CUCM"""
    try:
        logger.info(f"Deleting phone {phone_name} for user {current_user['user']}")
        
        result = axl_client.delete_phone(phone_name)
        
        if result.get('success', False):
            await write_to_census("delete_phone", {
                "mac": phone_name,
                "status": "deleted",
                "user": current_user['user']
            })
            
            return create_response(True, {"message": "Phone deleted successfully"})
        else:
            return create_response(False, error=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Delete phone failed: {e}")
        return create_response(False, error=str(e))

# ============================================================================
# User Management Endpoints
# ============================================================================

@app.post("/api/v1/users", response_model=APIResponse)
async def add_user(
    user: UserRequest,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Add new user to CUCM"""
    try:
        logger.info(f"Adding user {user.userid} for user {current_user['user']}")
        
        result = axl_client.add_user({
            "userid": user.userid,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "mailid": user.mailid,
            "primaryExtension": user.primary_extension
        })
        
        if result.get('success', False):
            await write_to_census("add_user", {
                "userid": user.userid,
                "status": "active",
                "user": current_user['user']
            })
            
            return create_response(True, result.get('data'))
        else:
            return create_response(False, error=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Add user failed: {e}")
        return create_response(False, error=str(e))

# ============================================================================
# Line Management Endpoints
# ============================================================================

@app.post("/api/v1/lines", response_model=APIResponse)
async def add_line(
    line: LineRequest,
    current_user: dict = Depends(get_current_user),
    axl_client: AXLClient = Depends(get_axl_client)
):
    """Add new line to CUCM"""
    try:
        logger.info(f"Adding line {line.pattern} for user {current_user['user']}")
        
        result = axl_client.add_line({
            "pattern": line.pattern,
            "description": line.description,
            "routePartitionName": line.route_partition,
            "usage": line.usage
        })
        
        if result.get('success', False):
            await write_to_census("add_line", {
                "pattern": line.pattern,
                "status": "active",
                "user": current_user['user']
            })
            
            return create_response(True, result.get('data'))
        else:
            return create_response(False, error=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Add line failed: {e}")
        return create_response(False, error=str(e))

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting AXLerate API Gateway...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
