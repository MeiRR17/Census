"""
CENSUS Database Models - SQLAlchemy 2.0
Stage 1: Base Infrastructure & Models
"""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, 
    Text, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Device(Base):
    """Represents a communication endpoint (IP Phone, Softphone, Jabber, etc.)."""
    
    __tablename__ = "devices"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # CUCM Identifiers
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Network Identity
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True, index=True)
    
    # Status & Ownership
    status: Mapped[str] = mapped_column(
        String(20), 
        default="unknown",
        index=True
    )  # registered, unregistered, rejected, unknown, partial
    
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=True
    )
    owner: Mapped[Optional["User"]] = relationship(back_populates="devices")
    
    # Line Associations
    lines: Mapped[List["DeviceLineAssociation"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    # Network Topology
    switch_connections: Mapped[List["SwitchConnection"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    # Cluster & Source Tracking
    cucm_cluster: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_seen_from_cucm: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    last_seen_from_scraper: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Vector embedding for semantic search
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(384), nullable=True)
    
    # Raw data storage
    raw_cucm_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    raw_scraper_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('ix_devices_status_cluster', 'status', 'cucm_cluster'),
    )


class Line(Base):
    """Represents a telephone line (DN - Directory Number)."""
    
    __tablename__ = "lines"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Line Identity
    directory_number: Mapped[str] = mapped_column(String(50), index=True)
    partition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Usage Info
    usage_profile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Device Associations
    device_associations: Mapped[List["DeviceLineAssociation"]] = relationship(
        back_populates="line",
        cascade="all, delete-orphan"
    )
    
    # CUCM Source
    cucm_cluster: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('directory_number', 'partition', 'cucm_cluster', 
                        name='uq_line_dn_partition_cluster'),
    )


class DeviceLineAssociation(Base):
    """Junction table linking Devices to Lines."""
    
    __tablename__ = "device_line_associations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("devices.id")
    )
    line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("lines.id")
    )
    
    # Association metadata
    line_index: Mapped[int] = mapped_column(Integer, default=1)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    device: Mapped["Device"] = relationship(back_populates="lines")
    line: Mapped["Line"] = relationship(back_populates="device_associations")
    
    __table_args__ = (
        UniqueConstraint('device_id', 'line_id', name='uq_device_line'),
    )


class User(Base):
    """Represents a person from Active Directory or HR system."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # AD Identity
    sam_account_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    distinguished_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    object_guid: Mapped[Optional[str]] = mapped_column(String(36), unique=True, nullable=True)
    
    # Profile Info
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    office: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    manager: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # AD Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_ad_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Relationships
    devices: Mapped[List["Device"]] = relationship(back_populates="owner")
    
    # Raw AD Data
    raw_ad_attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class SwitchConnection(Base):
    """Represents network topology data from CDP/LLDP scraping."""
    
    __tablename__ = "switch_connections"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Device Link
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("devices.id")
    )
    device: Mapped["Device"] = relationship(back_populates="switch_connections")
    
    # Switch Identity
    switch_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    switch_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    switch_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Port Information
    local_port: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    remote_port: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    port_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vlan: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Protocol
    discovery_protocol: Mapped[Optional[str]] = mapped_column(
        String(10), 
        nullable=True
    )  # CDP or LLDP
    
    # Timestamps
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Raw Data
    raw_scrape_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('ix_switch_conn_device', 'device_id', 'switch_name'),
    )


class SyncLog(Base):
    """Audit log for synchronization operations."""
    
    __tablename__ = "sync_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Sync Details
    sync_type: Mapped[str] = mapped_column(String(50))  # cucm, scraper, ad, full
    source: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))  # success, failed, partial
    
    # Statistics
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    records_orphaned: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Error Details
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
