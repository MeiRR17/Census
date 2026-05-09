#!/usr/bin/env python3
"""
CENSUS FastAPI Application
==========================

REST API for CENSUS database with pagination, filtering,
and comprehensive error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncpg
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Pydantic Models
# =============================================================================

@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 100
    max_page_size: int = 5000

class DeviceQueryParams(BaseModel):
    """Query parameters for device searches."""
    status: Optional[str] = Field(None, description="Filter by device status")
    device_type: Optional[str] = Field(None, description="Filter by device type")
    location_id: Optional[str] = Field(None, description="Filter by location")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    search: Optional[str] = Field(None, description="Search in device name or MAC")

class UserQueryParams(BaseModel):
    """Query parameters for user searches."""
    department: Optional[str] = Field(None, description="Filter by department")
    title: Optional[str] = Field(None, description="Filter by job title")
    account_enabled: Optional[bool] = Field(None, description="Filter by account status")
    search: Optional[str] = Field(None, description="Search in name, email, or department")

class LineQueryParams(BaseModel):
    """Query parameters for line searches."""
    partition: Optional[str] = Field(None, description="Filter by partition")
    calling_search_space: Optional[str] = Field(None, description="Filter by calling search space")
    device_pool: Optional[str] = Field(None, description="Filter by device pool")
    line_type: Optional[str] = Field(None, description="Filter by line type")
    endpoint_mac: Optional[str] = Field(None, description="Filter by endpoint MAC address")

class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool = True
    data: Any = None
    message: str = "Operation completed successfully"
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    error: Optional[str] = None

# =============================================================================
# Database Connection
# =============================================================================

class CENSUSDB:
    """CENSUS database manager with connection pooling."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("CENSUS database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize CENSUS DB: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool."""
        async with self.pool.acquire() as conn:
            yield conn
    
    async def get_devices_paginated(self, params: DeviceQueryParams, 
                                pagination: PaginationParams) -> Dict[str, Any]:
        """Get devices with pagination and filtering."""
        try:
            async with self.get_connection() as conn:
                # Build WHERE clause
                where_conditions = []
                query_args = []
                
                if params.status:
                    where_conditions.append("status = $%s")
                    query_args.append(params.status)
                
                if params.device_type:
                    where_conditions.append("device_type = $%s")
                    query_args.append(params.device_type)
                
                if params.location_id:
                    where_conditions.append("location_id = $%s")
                    query_args.append(params.location_id)
                
                if params.user_id:
                    where_conditions.append("user_id = $%s")
                    query_args.append(params.user_id)
                
                if params.search:
                    where_conditions.append("(device_name ILIKE $%s OR mac_address ILIKE $%s)")
                    query_args.extend([f"%{params.search}%", f"%{params.search}%"])
                
                # Combine WHERE conditions
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM devices WHERE {where_clause}
                """
                total_count = await conn.fetchval(count_query, *query_args)
                
                # Calculate pagination
                offset = (pagination.page - 1) * pagination.page_size
                limit = min(pagination.page_size, pagination.max_page_size)
                
                # Get paginated results
                data_query = f"""
                    SELECT id, mac_address, device_name, device_type, model, 
                           status, user_id, location_id, created_at, updated_at,
                           last_seen, firmware_version, ip_address
                    FROM devices 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT $%s OFFSET $%s
                """
                
                devices = await conn.fetch(data_query, *query_args, limit, offset)
                
                return {
                    "devices": [dict(device) for device in devices],
                    "pagination": {
                        "page": pagination.page,
                        "page_size": len(devices),
                        "total_count": total_count,
                        "total_pages": (total_count + pagination.page_size - 1) // pagination.page_size + 1,
                        "has_next": offset + len(devices) < total_count
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_users_paginated(self, params: UserQueryParams, 
                              pagination: PaginationParams) -> Dict[str, Any]:
        """Get users with pagination and filtering."""
        try:
            async with self.get_connection() as conn:
                # Build WHERE clause
                where_conditions = []
                query_args = []
                
                if params.department:
                    where_conditions.append("department = $%s")
                    query_args.append(params.department)
                
                if params.title:
                    where_conditions.append("title = $%s")
                    query_args.append(params.title)
                
                if params.account_enabled is not None:
                    where_conditions.append("account_enabled = $%s")
                    query_args.append(params.account_enabled)
                
                if params.search:
                    where_conditions.append("(full_name ILIKE $%s OR email ILIKE $%s OR department ILIKE $%s)")
                    query_args.extend([f"%{params.search}%", f"%{params.search}%", f"%{params.search}%"])
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM users WHERE {where_clause}
                """
                total_count = await conn.fetchval(count_query, *query_args)
                
                # Calculate pagination
                offset = (pagination.page - 1) * pagination.page_size
                limit = min(pagination.page_size, pagination.max_page_size)
                
                # Get paginated results
                data_query = f"""
                    SELECT id, userid, full_name, email, department, title,
                           phone_number, manager, groups, account_enabled,
                           last_logon, created_at, updated_at
                    FROM users 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT $%s OFFSET $%s
                """
                
                users = await conn.fetch(data_query, *query_args, limit, offset)
                
                return {
                    "users": [dict(user) for user in users],
                    "pagination": {
                        "page": pagination.page,
                        "page_size": len(users),
                        "total_count": total_count,
                        "total_pages": (total_count + pagination.page_size - 1) // pagination.page_size + 1,
                        "has_next": offset + len(users) < total_count
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_lines_paginated(self, params: LineQueryParams, 
                             pagination: PaginationParams) -> Dict[str, Any]:
        """Get telephony lines with pagination and filtering."""
        try:
            async with self.get_connection() as conn:
                # Build WHERE clause
                where_conditions = []
                query_args = []
                
                if params.partition:
                    where_conditions.append("partition = $%s")
                    query_args.append(params.partition)
                
                if params.calling_search_space:
                    where_conditions.append("calling_search_space = $%s")
                    query_args.append(params.calling_search_space)
                
                if params.device_pool:
                    where_conditions.append("device_pool = $%s")
                    query_args.append(params.device_pool)
                
                if params.line_type:
                    where_conditions.append("line_type = $%s")
                    query_args.append(params.line_type)
                
                if params.endpoint_mac:
                    where_conditions.append("endpoint_mac = $%s")
                    query_args.append(params.endpoint_mac)
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM telephony_lines WHERE {where_clause}
                """
                total_count = await conn.fetchval(count_query, *query_args)
                
                # Calculate pagination
                offset = (pagination.page - 1) * pagination.page_size
                limit = min(pagination.page_size, pagination.max_page_size)
                
                # Get paginated results
                data_query = f"""
                    SELECT id, directory_number, partition, calling_search_space,
                           device_pool, route_pattern, endpoint_mac, is_active,
                           line_type, created_at, updated_at
                    FROM telephony_lines 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT $%s OFFSET $%s
                """
                
                lines = await conn.fetch(data_query, *query_args, limit, offset)
                
                return {
                    "lines": [dict(line) for line in lines],
                    "pagination": {
                        "page": pagination.page,
                        "page_size": len(lines),
                        "total_count": total_count,
                        "total_pages": (total_count + pagination.page_size - 1) // pagination.page_size + 1,
                        "has_next": offset + len(lines) < total_count
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get lines: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("CENSUS database connection closed")

# =============================================================================
# FastAPI Application
# =============================================================================

# Initialize FastAPI
app = FastAPI(
    title="CENSUS API",
    description="REST API for CENSUS telephony database",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Global database instance
census_db = None

async def get_census_db() -> CENSUSDB:
    """Get CENSUS database instance."""
    global census_db
    if census_db is None:
        db_url = os.getenv("CENSUS_DB_URL", "postgresql://census_user:census_password@localhost:5432/census_db")
        census_db = CENSUSDB(db_url)
        await census_db.initialize()
    return census_db

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint."""
    try:
        async with census_db.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return APIResponse(
                data={"status": "healthy", "database": "connected"},
                message="CENSUS API is healthy"
            )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Health check failed: {str(e)}",
            message="Service unavailable"
        )

@app.get("/devices", response_model=APIResponse)
async def get_devices(
    status: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=5000),
    db: CENSUSDB = Depends(get_census_db)
):
    """Get devices with pagination and filtering."""
    try:
        params = DeviceQueryParams(
            status=status,
            device_type=device_type,
            location_id=location_id,
            user_id=user_id,
            search=search
        )
        
        pagination = PaginationParams(
            page=page,
            page_size=page_size
        )
        
        result = await db.get_devices_paginated(params, pagination)
        
        return APIResponse(
            data=result,
            total_count=result["pagination"]["total_count"],
            page=pagination.page,
            page_size=len(result["devices"])
        )
        
    except Exception as e:
        logger.error(f"Get devices failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices/{mac_address}", response_model=APIResponse)
async def get_device(mac_address: str, db: CENSUSDB = Depends(get_census_db)):
    """Get specific device by MAC address."""
    try:
        async with db.get_connection() as conn:
            device = await conn.fetchrow("""
                SELECT id, mac_address, device_name, device_type, model, status,
                       user_id, location_id, created_at, updated_at, last_seen,
                       firmware_version, ip_address
                FROM devices 
                WHERE mac_address = $1
            """, mac_address)
            
            if device:
                return APIResponse(data=dict(device))
            else:
                return APIResponse(
                    success=False,
                    error="Device not found",
                    message=f"Device with MAC {mac_address} not found"
                )
                
    except Exception as e:
        logger.error(f"Get device failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users", response_model=APIResponse)
async def get_users(
    department: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    account_enabled: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=5000),
    db: CENSUSDB = Depends(get_census_db)
):
    """Get users with pagination and filtering."""
    try:
        params = UserQueryParams(
            department=department,
            title=title,
            account_enabled=account_enabled,
            search=search
        )
        
        pagination = PaginationParams(
            page=page,
            page_size=page_size
        )
        
        result = await db.get_users_paginated(params, pagination)
        
        return APIResponse(
            data=result,
            total_count=result["pagination"]["total_count"],
            page=pagination.page,
            page_size=len(result["users"])
        )
        
    except Exception as e:
        logger.error(f"Get users failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lines", response_model=APIResponse)
async def get_lines(
    partition: Optional[str] = Query(None),
    calling_search_space: Optional[str] = Query(None),
    device_pool: Optional[str] = Query(None),
    line_type: Optional[str] = Query(None),
    endpoint_mac: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=5000),
    db: CENSUSDB = Depends(get_census_db)
):
    """Get telephony lines with pagination and filtering."""
    try:
        params = LineQueryParams(
            partition=partition,
            calling_search_space=calling_search_space,
            device_pool=device_pool,
            line_type=line_type,
            endpoint_mac=endpoint_mac
        )
        
        pagination = PaginationParams(
            page=page,
            page_size=page_size
        )
        
        result = await db.get_lines_paginated(params, pagination)
        
        return APIResponse(
            data=result,
            total_count=result["pagination"]["total_count"],
            page=pagination.page,
            page_size=len(result["lines"])
        )
        
    except Exception as e:
        logger.error(f"Get lines failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=APIResponse)
async def get_statistics(db: CENSUSDB = Depends(get_census_db)):
    """Get database statistics."""
    try:
        async with db.get_connection() as conn:
            # Device statistics
            device_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_devices,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_devices,
                    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_devices,
                    COUNT(CASE WHEN last_seen > NOW() - INTERVAL '24 hours' THEN 1 END) as devices_seen_24h
                FROM devices
            """)
            
            # User statistics
            user_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN account_enabled = true THEN 1 END) as active_users,
                    COUNT(CASE WHEN last_logon > NOW() - INTERVAL '7 days' THEN 1 END) as users_active_7d
                FROM users
            """)
            
            # Line statistics
            line_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_lines,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_lines,
                    COUNT(DISTINCT partition) as partitions_used
                FROM telephony_lines
            """)
            
            return APIResponse(
                data={
                    "devices": dict(device_stats) if device_stats else {},
                    "users": dict(user_stats) if user_stats else {},
                    "lines": dict(line_stats) if line_stats else {}
                },
                message="Statistics retrieved successfully"
            )
            
    except Exception as e:
        logger.error(f"Get statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Startup and Shutdown
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("CENSUS API starting up...")
    db = await get_census_db()
    logger.info("CENSUS API ready to serve requests")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("CENSUS API shutting down...")
    if census_db:
        await census_db.close()

if __name__ == "__main__":
    import uvicorn
    import os
    
    uvicorn.run(
        "census:app",
        host="0.0.0.0",
        port=int(os.getenv("CENSUS_PORT", "8001")),
        log_level="info"
    )
