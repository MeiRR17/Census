"""
CENSUS API Schemas - Pydantic V2 models for request/response serialization.
Defines the data contracts between frontend and backend.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base response model with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseResponse):
    """User information response schema."""
    id: UUID
    sam_account_name: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationResponse(BaseResponse):
    """Location information response schema."""
    id: UUID
    building_name: Optional[str] = None
    room_number: Optional[str] = None
    switch_ip: Optional[str] = None
    subnet: Optional[str] = None


class SwitchConnectionResponse(BaseResponse):
    """Switch connection information response schema."""
    switch_name: Optional[str] = None
    switch_ip: Optional[str] = None
    remote_port: Optional[str] = None
    vlan: Optional[str] = None


class LineResponse(BaseResponse):
    """Telephone line information response schema."""
    directory_number: str
    partition: Optional[str] = None
    css: Optional[str] = None  # Mapped from usage_profile
    device_pool: Optional[str] = None  # Mapped from cucm_cluster
    
    @classmethod
    def from_line(cls, line):
        """Create LineResponse from Line model with field mapping."""
        return cls(
            directory_number=line.directory_number,
            partition=line.partition,
            css=line.usage_profile,  # Map usage_profile to css
            device_pool=line.cucm_cluster  # Map cucm_cluster to device_pool
        )


class DeviceResponse(BaseResponse):
    """Device/Endpoint information response schema."""
    mac_address: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
    updated_at: datetime
    
    # Nested relationships
    owner: Optional[UserResponse] = None
    switch_connections: List[SwitchConnectionResponse] = []
    lines: List[LineResponse] = []
    
    @classmethod
    def from_device(cls, device):
        """Create DeviceResponse from Device model with proper field mapping."""
        # Transform nested relationships safely
        owner = None
        if device.owner:
            owner = UserResponse(
                id=device.owner.id,
                sam_account_name=device.owner.sam_account_name,
                display_name=device.owner.display_name,
                department=device.owner.department,
                is_active=device.owner.is_active,
                created_at=device.owner.created_at,
                updated_at=device.owner.updated_at
            )
        
        switch_connections = []
        for sc in device.switch_connections or []:
            switch_connections.append(
                SwitchConnectionResponse(
                    switch_name=sc.switch_name,
                    switch_ip=sc.switch_ip,
                    remote_port=sc.remote_port,
                    vlan=sc.vlan
                )
            )
        
        lines = []
        for device_line in device.lines or []:
            if device_line.line:
                lines.append(LineResponse.from_line(device_line.line))
        
        return cls(
            mac_address=device.mac_address,
            device_type=device.device_type,
            model=device.model,
            ip_address=device.ip_address,
            status=device.status,
            updated_at=device.updated_at,
            owner=owner,
            switch_connections=switch_connections,
            lines=lines
        )


class DeviceLineAssociationResponse(BaseResponse):
    """Device-line association response schema."""
    id: UUID
    device_id: UUID
    line_id: UUID
    line_index: int
    is_primary: bool
    device: Optional[DeviceResponse] = None
    line: Optional[LineResponse] = None


class SyncLogResponse(BaseResponse):
    """Synchronization log response schema."""
    id: UUID
    sync_type: str
    source: str
    status: str
    records_processed: int
    records_created: int
    records_updated: int
    records_failed: int
    records_orphaned: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class CUCMPhoneCreateRequest(BaseModel):
    """Request schema for creating a new CUCM phone with all possible fields."""
    mac_address: str  # Required: MAC address (e.g., "00:11:22:33:44:55")
    description: Optional[str] = "New Phone"
    model: Optional[str] = "Cisco 7841"
    ip_address: Optional[str] = "10.1.1.200"
    device_pool: Optional[str] = "Default"
    calling_search_space: Optional[str] = "CSS-Internal"
    line_dn: Optional[str] = ""  # Directory Number
    line_partition: Optional[str] = "PT-Internal"
    status: Optional[str] = "unregistered"  # registered, unregistered, rejected


class SyncTriggerResponse(BaseModel):
    """Sync trigger response schema."""
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    """Current sync status response schema."""
    is_syncing: bool
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    total_devices: int
    total_users: int
    registered_devices: int
    unregistered_devices: int


class DeviceStatsResponse(BaseModel):
    """Device statistics response schema."""
    total_devices: int
    registered_devices: int
    unregistered_devices: int
    by_device_type: dict[str, int]
    by_model: dict[str, int]
    by_status: dict[str, int]


class UserStatsResponse(BaseModel):
    """User statistics response schema."""
    total_users: int
    active_users: int
    inactive_users: int
    by_department: dict[str, int]


class NetworkStatsResponse(BaseModel):
    """Network topology statistics response schema."""
    total_switches: int
    devices_with_topology: int
    devices_without_topology: int
    by_switch: dict[str, int]
    by_vlan: dict[str, int]


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    service: str
    version: str
    database: str
    timestamp: datetime


# Request schemas (for future POST/PUT operations)
class UserCreateRequest(BaseModel):
    """User creation request schema."""
    ad_username: str
    display_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """User update request schema."""
    display_name: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceUpdateRequest(BaseModel):
    """Device update request schema."""
    description: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None


# Filter schemas for query parameters
class DeviceFilter(BaseModel):
    """Device filter parameters."""
    mac_address: Optional[str] = None
    device_type: Optional[str] = None
    is_registered: Optional[bool] = None
    status: Optional[str] = None
    cucm_cluster: Optional[str] = None


class UserFilter(BaseModel):
    """User filter parameters."""
    department: Optional[str] = None
    is_active: Optional[bool] = None
    ad_username: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    size: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "asc"


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[BaseModel]
    total: int
    page: int
    size: int
    pages: int
