"""
CENSUS API Router - FastAPI endpoints for census data operations.
Exposes device, user, and synchronization endpoints to the frontend.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.session import get_db
from database.models import Device, User, SwitchConnection, SyncLog, Line, DeviceLineAssociation
from schemas.census import (
    DeviceResponse, UserResponse, SwitchConnectionResponse, LineResponse,
    SyncTriggerResponse, SyncStatusResponse, DeviceStatsResponse,
    UserStatsResponse, NetworkStatsResponse, HealthResponse,
    SyncLogResponse, LocationResponse
)
from services.sync_engine import run_full_sync
from ciscoaxl import axl


logger = logging.getLogger(__name__)

# Create FastAPI router
census_router = APIRouter(
    prefix="/api/v1/census",
    tags=["Census"],
    responses={404: {"description": "Not found"}}
)


# Global sync state tracking (in production, use Redis or database)
_sync_state = {
    "is_syncing": False,
    "last_sync": None,
    "last_sync_status": None
}


@census_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for Census API.
    
    Returns:
        HealthResponse: Service health status
    """
    try:
        # Check database connectivity
        result = await db.execute(select(func.count()).select_from(User))
        user_count = result.scalar() or 0
        
        db_status = "connected" if user_count >= 0 else "error"
        
        return HealthResponse(
            status="ok",
            service="CENSUS",
            version="1.0.0",
            database=db_status,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@census_router.get("/endpoints", response_model=List[DeviceResponse], tags=["Devices"])
async def get_endpoints(
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch all endpoints/devices with nested relationships.
    
    Args:
        db: Database session
        
    Returns:
        List[DeviceResponse]: List of devices with owner, switch connections, and lines
    """
    try:
        # Build base query with eager loading to prevent N+1 queries
        query = select(Device).options(
            selectinload(Device.owner),
            selectinload(Device.switch_connections),
            selectinload(Device.lines).selectinload(DeviceLineAssociation.line)
        ).order_by(Device.name)
        
        # Execute query
        result = await db.execute(query)
        devices = result.scalars().all()
        
        # Transform devices using the from_device method
        device_responses = [DeviceResponse.from_device(device) for device in devices]
        
        logger.info(f"Retrieved {len(device_responses)} devices with relationships")
        return device_responses
        
    except Exception as e:
        logger.error(f"Failed to fetch endpoints: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch endpoints")


@census_router.get("/endpoints/{device_id}", response_model=DeviceResponse, tags=["Devices"])
async def get_endpoint(device_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch a specific endpoint by ID.
    
    Args:
        device_id: Device UUID
        db: Database session
        
    Returns:
        DeviceResponse: Device details
    """
    try:
        import uuid
        device_uuid = uuid.UUID(device_id)
        
        query = select(Device).options(
            selectinload(Device.owner),
            selectinload(Device.switch_connections)
        ).where(Device.id == device_uuid)
        
        result = await db.execute(query)
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return device
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID format")
    except Exception as e:
        logger.error(f"Failed to fetch endpoint {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch endpoint")


@census_router.get("/users", response_model=List[UserResponse], tags=["Users"])
async def get_users(
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch all active users.
    
    Args:
        db: Database session
        
    Returns:
        List[UserResponse]: List of active users
    """
    try:
        # Build base query - filter for active users only
        query = select(User).where(User.is_active == True).order_by(User.sam_account_name)
        
        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Transform users using Pydantic's from_attributes (which uses model_config)
        user_responses = [UserResponse.model_validate(user, from_attributes=True) for user in users]
        
        logger.info(f"Retrieved {len(user_responses)} active users")
        return user_responses
        
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@census_router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetch a specific user by ID.
    
    Args:
        user_id: User UUID
        db: Database session
        
    Returns:
        UserResponse: User details
    """
    try:
        import uuid
        user_uuid = uuid.UUID(user_id)
        
        query = select(User).where(User.id == user_uuid)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")


@census_router.get("/switch-connections", response_model=List[SwitchConnectionResponse], tags=["Network"])
async def get_switch_connections(
    db: AsyncSession = Depends(get_db),
    switch_name: Optional[str] = Query(None, description="Filter by switch name"),
    limit: int = Query(1000, le=10000, description="Maximum number of results")
):
    """
    Fetch all switch connections with optional filtering.
    
    Args:
        db: Database session
        switch_name: Filter by switch name (partial match)
        limit: Maximum number of results to return
        
    Returns:
        List[SwitchConnectionResponse]: List of switch connections
    """
    try:
        # Build base query with relationships
        query = select(SwitchConnection).options(
            selectinload(SwitchConnection.device)
        )
        
        # Apply filters
        if switch_name:
            query = query.where(SwitchConnection.switch_name.ilike(f"%{switch_name}%"))
        
        # Apply ordering and limit
        query = query.order_by(SwitchConnection.switch_name, SwitchConnection.remote_port).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        connections = result.scalars().all()
        
        logger.info(f"Retrieved {len(connections)} switch connections")
        return connections
        
    except Exception as e:
        logger.error(f"Failed to fetch switch connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch switch connections")


@census_router.get("/locations", response_model=List[LocationResponse], tags=["Locations"])
async def get_locations(
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch all locations.
    
    Args:
        db: Database session
        
    Returns:
        List[LocationResponse]: List of locations
    """
    try:
        # Since Location model doesn't exist in database yet, return empty list
        # This will be implemented when Location model is added in future phases
        logger.info("Retrieved 0 locations (Location model not yet implemented)")
        return []
        
    except Exception as e:
        logger.error(f"Failed to fetch locations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch locations")


@census_router.post("/sync", response_model=SyncTriggerResponse, tags=["Synchronization"])
async def trigger_sync(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger a full synchronization in the background.
    
    Args:
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        SyncTriggerResponse: Sync trigger status
    """
    try:
        # Add real sync task to background
        background_tasks.add_task(run_full_sync, db)
        
        logger.info("Real synchronization triggered in background")
        return SyncTriggerResponse(
            status="processing",
            message="Sync started in background"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger synchronization")


@census_router.get("/sync/status", response_model=SyncStatusResponse, tags=["Synchronization"])
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """
    Get current synchronization status and statistics.
    
    Args:
        db: Database session
        
    Returns:
        SyncStatusResponse: Current sync status
    """
    try:
        global _sync_state
        
        # Get statistics
        device_count = await db.scalar(select(func.count()).select_from(Device))
        user_count = await db.scalar(select(func.count()).select_from(User))
        registered_count = await db.scalar(
            select(func.count()).select_from(Device).where(Device.status == "registered")
        )
        
        return SyncStatusResponse(
            is_syncing=_sync_state["is_syncing"],
            last_sync=_sync_state["last_sync"],
            last_sync_status=_sync_state["last_sync_status"],
            total_devices=device_count or 0,
            total_users=user_count or 0,
            registered_devices=registered_count or 0,
            unregistered_devices=(device_count or 0) - (registered_count or 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync status")


@census_router.get("/stats/devices", response_model=DeviceStatsResponse, tags=["Statistics"])
async def get_device_stats(db: AsyncSession = Depends(get_db)):
    """
    Get device statistics and breakdowns.
    
    Args:
        db: Database session
        
    Returns:
        DeviceStatsResponse: Device statistics
    """
    try:
        # Total devices
        total_devices = await db.scalar(select(func.count()).select_from(Device))
        
        # Registration status
        registered_devices = await db.scalar(
            select(func.count()).select_from(Device).where(Device.status == "registered")
        )
        unregistered_devices = (total_devices or 0) - (registered_devices or 0)
        
        # By device type
        device_type_result = await db.execute(
            select(Device.device_type, func.count().label("count"))
            .group_by(Device.device_type)
            .where(Device.device_type.isnot(None))
        )
        by_device_type = {row.device_type: row.count for row in device_type_result}
        
        # By model
        model_result = await db.execute(
            select(Device.model, func.count().label("count"))
            .group_by(Device.model)
            .where(Device.model.isnot(None))
            .limit(20)  # Limit to top 20 models
        )
        by_model = {row.model: row.count for row in model_result}
        
        # By status
        status_result = await db.execute(
            select(Device.status, func.count().label("count"))
            .group_by(Device.status)
        )
        by_status = {row.status: row.count for row in status_result}
        
        return DeviceStatsResponse(
            total_devices=total_devices or 0,
            registered_devices=registered_devices or 0,
            unregistered_devices=unregistered_devices,
            by_device_type=by_device_type,
            by_model=by_model,
            by_status=by_status
        )
        
    except Exception as e:
        logger.error(f"Failed to get device stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device statistics")


@census_router.get("/stats/users", response_model=UserStatsResponse, tags=["Statistics"])
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    """
    Get user statistics and breakdowns.
    
    Args:
        db: Database session
        
    Returns:
        UserStatsResponse: User statistics
    """
    try:
        # Total users
        total_users = await db.scalar(select(func.count()).select_from(User))
        
        # Active status
        active_users = await db.scalar(
            select(func.count()).select_from(User).where(User.is_active == True)
        )
        inactive_users = (total_users or 0) - (active_users or 0)
        
        # By department
        dept_result = await db.execute(
            select(User.department, func.count().label("count"))
            .group_by(User.department)
            .where(User.department.isnot(None))
            .limit(20)  # Limit to top 20 departments
        )
        by_department = {row.department: row.count for row in dept_result}
        
        return UserStatsResponse(
            total_users=total_users or 0,
            active_users=active_users or 0,
            inactive_users=inactive_users,
            by_department=by_department
        )
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")


@census_router.get("/stats/network", response_model=NetworkStatsResponse, tags=["Statistics"])
async def get_network_stats(db: AsyncSession = Depends(get_db)):
    """
    Get network topology statistics.
    
    Args:
        db: Database session
        
    Returns:
        NetworkStatsResponse: Network statistics
    """
    try:
        # Total switches (unique switch names)
        switch_count_result = await db.execute(
            select(func.count(func.distinct(SwitchConnection.switch_name)))
            .where(SwitchConnection.switch_name.isnot(None))
        )
        total_switches = switch_count_result.scalar() or 0
        
        # Devices with/without topology
        devices_with_topology = await db.scalar(
            select(func.count(func.distinct(SwitchConnection.device_id)))
        )
        total_devices = await db.scalar(select(func.count()).select_from(Device))
        devices_without_topology = (total_devices or 0) - (devices_with_topology or 0)
        
        # By switch
        switch_result = await db.execute(
            select(SwitchConnection.switch_name, func.count().label("count"))
            .group_by(SwitchConnection.switch_name)
            .where(SwitchConnection.switch_name.isnot(None))
            .order_by(func.count().desc())
            .limit(20)  # Top 20 switches
        )
        by_switch = {row.switch_name: row.count for row in switch_result}
        
        # By VLAN
        vlan_result = await db.execute(
            select(SwitchConnection.vlan, func.count().label("count"))
            .group_by(SwitchConnection.vlan)
            .where(SwitchConnection.vlan.isnot(None))
            .order_by(func.count().desc())
            .limit(20)  # Top 20 VLANs
        )
        by_vlan = {row.vlan: row.count for row in vlan_result}
        
        return NetworkStatsResponse(
            total_switches=total_switches,
            devices_with_topology=devices_with_topology or 0,
            devices_without_topology=devices_without_topology,
            by_switch=by_switch,
            by_vlan=by_vlan
        )
        
    except Exception as e:
        logger.error(f"Failed to get network stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get network statistics")


@census_router.get("/sync/logs", response_model=List[SyncLogResponse], tags=["Synchronization"])
async def get_sync_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=500, description="Maximum number of logs to return")
):
    """
    Get synchronization logs.
    
    Args:
        db: Database session
        limit: Maximum number of logs to return
        
    Returns:
        List[SyncLogResponse]: List of sync logs
    """
    try:
        query = select(SyncLog).order_by(SyncLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return logs
        
    except Exception as e:
        logger.error(f"Failed to get sync logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync logs")
