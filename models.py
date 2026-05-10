"""
Census Data Models - SQLAlchemy models for database schemas
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, text
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

# =====================================================
# CUCM Models
# =====================================================

class CUCMPhone(Base):
    """CUCM Phone/Device Model"""
    __tablename__ = 'cucm_phones'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String)
    product_name = Column(String(100))
    model = Column(String(100))
    protocol = Column(String(50), default='SIP')
    ip_address = Column(INET)
    mac_address = Column(String(17))
    device_pool = Column(String(100))
    calling_search_space = Column(String(100))
    device_security_profile = Column(String(100))
    sip_profile = Column(String(100))
    location = Column(String(100))
    status = Column(String(50), default='registered')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSONB)
    
    # Simplified representation
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'name': self.name,
            'description': self.description,
            'product_name': self.product_name,
            'model': self.model,
            'protocol': self.protocol,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'mac_address': self.mac_address,
            'device_pool': self.device_pool,
            'calling_search_space': self.calling_search_space,
            'location': self.location,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CUCMLine(Base):
    """CUCM Line Model"""
    __tablename__ = 'cucm_lines'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    pattern = Column(String(50), nullable=False)
    description = Column(String)
    route_partition = Column(String(100))
    calling_search_space = Column(String(100))
    max_num_calls = Column(Integer, default=2)
    busy_trigger = Column(Integer, default=1)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSONB)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': str(self.uuid),
            'pattern': self.pattern,
            'description': self.description,
            'route_partition': self.route_partition,
            'calling_search_space': self.calling_search_space,
            'max_num_calls': self.max_num_calls,
            'busy_trigger': self.busy_trigger,
            'status': self.status
        }

class CUCMUser(Base):
    """CUCM User Model"""
    __tablename__ = 'cucm_users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    mail_id = Column(String(255))
    telephone_number = Column(String(50))
    mobile_number = Column(String(50))
    department = Column(String(100))
    manager = Column(String(255))
    title = Column(String(100))
    associated_devices = Column(JSONB)  # Array of device UUIDs
    associated_lines = Column(JSONB)  # Array of line UUIDs
    user_groups = Column(JSONB)  # Array of group names
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSONB)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'mail_id': self.mail_id,
            'telephone_number': self.telephone_number,
            'department': self.department,
            'title': self.title,
            'status': self.status
        }

# =====================================================
# CMS Models
# =====================================================

class CMSCoSpace(Base):
    """CMS CoSpace Model"""
    __tablename__ = 'cms_cospaces'
    
    id = Column(Integer, primary_key=True)
    cospace_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    uri = Column(String(255))
    description = Column(String)
    passcode = Column(String(100))
    auto_attendant = Column(Boolean, default=False)
    owner_id = Column(String(255))
    owner_name = Column(String(255))
    access_level = Column(String(50), default='PUBLIC')
    cospace_type = Column(String(50), default='MEETING')
    max_participants = Column(Integer, default=50)
    max_video_resolution = Column(String(50), default='HD')
    enable_chat = Column(Boolean, default=True)
    enable_recording = Column(Boolean, default=False)
    enable_live_streaming = Column(Boolean, default=False)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSONB)
    
    # Relationships
    calls = relationship("CMSCall", back_populates="cospace")
    
    def to_dict(self):
        return {
            'id': self.id,
            'cospace_id': self.cospace_id,
            'name': self.name,
            'uri': self.uri,
            'description': self.description,
            'passcode': self.passcode,
            'auto_attendant': self.auto_attendant,
            'owner_name': self.owner_name,
            'access_level': self.access_level,
            'max_participants': self.max_participants,
            'enable_recording': self.enable_recording,
            'status': self.status
        }

class CMSCall(Base):
    """CMS Call Model"""
    __tablename__ = 'cms_calls'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(String(255), unique=True, nullable=False)
    cospace_id = Column(String(255), ForeignKey('cms_cospaces.cospace_id'))
    cospace_name = Column(String(255))
    cospace_uri = Column(String(255))
    call_type = Column(String(50), default='MEETING')
    call_state = Column(String(50), default='ACTIVE')
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Integer, default=0)
    host_user_id = Column(String(255))
    host_user_name = Column(String(255))
    current_participants = Column(Integer, default=0)
    max_participants = Column(Integer, default=50)
    enable_chat = Column(Boolean, default=True)
    enable_recording = Column(Boolean, default=False)
    enable_live_streaming = Column(Boolean, default=False)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSONB)
    
    # Relationships
    cospace = relationship("CMSCoSpace", back_populates="calls")
    participants = relationship("CMSCallParticipant", back_populates="call")
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'cospace_id': self.cospace_id,
            'cospace_name': self.cospace_name,
            'call_state': self.call_state,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'host_user_name': self.host_user_name,
            'current_participants': self.current_participants,
            'status': self.status
        }

class CMSCallParticipant(Base):
    """CMS Call Participant Model"""
    __tablename__ = 'cms_call_participants'
    
    id = Column(Integer, primary_key=True)
    participant_id = Column(String(255), unique=True, nullable=False)
    call_id = Column(String(255), ForeignKey('cms_calls.call_id'))
    cospace_id = Column(String(255))
    participant_name = Column(String(255))
    participant_email = Column(String(255))
    participant_role = Column(String(50), default='PARTICIPANT')
    participant_status = Column(String(50), default='CONNECTED')
    join_time = Column(DateTime)
    leave_time = Column(DateTime)
    duration = Column(Integer, default=0)
    leg_id = Column(String(255))
    is_host = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    is_presenter = Column(Boolean, default=False)
    is_muted = Column(Boolean, default=False)
    is_video_muted = Column(Boolean, default=False)
    is_content_sharing = Column(Boolean, default=False)
    status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSONB)
    
    # Relationships
    call = relationship("CMSCall", back_populates="participants")
    
    def to_dict(self):
        return {
            'id': self.id,
            'participant_id': self.participant_id,
            'call_id': self.call_id,
            'participant_name': self.participant_name,
            'participant_email': self.participant_email,
            'participant_role': self.participant_role,
            'participant_status': self.participant_status,
            'join_time': self.join_time.isoformat() if self.join_time else None,
            'is_host': self.is_host,
            'is_moderator': self.is_moderator,
            'is_muted': self.is_muted,
            'leg_id': self.leg_id
        }

# =====================================================
# Legacy Models (for backward compatibility)
# =====================================================

class Device(Base):
    """Legacy Device Model"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    ip_address = Column(INET)
    mac_address = Column(String(17))
    device_type = Column(String(100))
    status = Column(String(50), default='unknown')
    source = Column(String(50), nullable=False)
    raw_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Meeting(Base):
    """Legacy Meeting Model"""
    __tablename__ = 'meetings'
    
    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    uri = Column(String(255))
    passcode = Column(String(100))
    status = Column(String(50), default='active')
    participants = Column(Integer, default=0)
    raw_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    """Legacy User Model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    department = Column(String(100))
    phone = Column(String(50))
    raw_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
