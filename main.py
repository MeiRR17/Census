"""
Census Clean - Clean, organized main application
"""
# Import the application
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from contextlib import contextmanager

# Import our organized modules
from sync import SyncManager, SyncMiddleware
from clients import *
from api_routers import cms_router, cucm_router, uccx_router, meetingplace_router, unified_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple configuration
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://census_user:census_password@localhost:5432/census_db")
    
    # System configurations
    SYSTEMS = {
        "cucm": {
            "host": os.getenv("CUCM_HOST", ""),
            "username": os.getenv("CUCM_USERNAME", ""),
            "password": os.getenv("CUCM_PASSWORD", "")
        },
        "cms": {
            "host": os.getenv("CMS_HOST", ""),
            "username": os.getenv("CMS_USERNAME", ""),
            "password": os.getenv("CMS_PASSWORD", "")
        },
        "meetingplace": {
            "host": os.getenv("MEETINGPLACE_HOST", ""),
            "username": os.getenv("MEETINGPLACE_USERNAME", ""),
            "password": os.getenv("MEETINGPLACE_PASSWORD", "")
        },
        "uccx": {
            "host": os.getenv("UCCX_HOST", ""),
            "username": os.getenv("UCCX_USERNAME", ""),
            "password": os.getenv("UCCX_PASSWORD", "")
        },
        "expressway": {
            "host": os.getenv("EXPRESSWAY_HOST", ""),
            "username": os.getenv("EXPRESSWAY_USERNAME", ""),
            "password": os.getenv("EXPRESSWAY_PASSWORD", "")
        },
        "sbc": {
            "host": os.getenv("SBC_HOST", ""),
            "username": os.getenv("SBC_USERNAME", ""),
            "password": os.getenv("SBC_PASSWORD", "")
        },
        "tgw": {
            "host": os.getenv("TGW_HOST", ""),
            "username": os.getenv("TGW_USERNAME", ""),
            "password": os.getenv("TGW_PASSWORD", "")
        }
    }

# Database setup
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Data models
class Device(BaseModel):
    id: Optional[int] = None
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: str
    status: str = "unknown"
    source: str
    raw_data: Optional[Dict[str, Any]] = None

class Meeting(BaseModel):
    id: Optional[int] = None
    meeting_id: str
    name: str
    uri: Optional[str] = None
    passcode: Optional[str] = None
    status: str = "active"
    participants: int = 0
    source: str
    raw_data: Optional[Dict[str, Any]] = None

class User(BaseModel):
    id: Optional[int] = None
    user_id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    source: str
    raw_data: Optional[Dict[str, Any]] = None

# FastAPI app
app = FastAPI(
    title="Census Clean",
    description="Organized bridge between edge apps and Cisco/Oracle servers",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(cms_router)
app.include_router(cucm_router)
app.include_router(uccx_router)
app.include_router(meetingplace_router)
app.include_router(unified_router)

# Initialize sync components
sync_manager = None
sync_middleware = None

def init_sync_components():
    """Initialize sync manager and middleware"""
    global sync_manager, sync_middleware
    
    try:
        sync_manager = SyncManager(Config.SYSTEMS, engine)
        sync_middleware = SyncMiddleware(Config.SYSTEMS, engine)
        logger.info("Sync components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize sync components: {e}")

# Database initialization
def init_db():
    """Initialize comprehensive database schemas for CUCM and CMS"""
    with engine.connect() as conn:
        # Execute the comprehensive schema SQL file
        schema_path = os.path.join(os.path.dirname(__file__), 'database_schemas.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                conn.execute(text(f.read()))
            logger.info("Loaded comprehensive database schemas from database_schemas.sql")
        else:
            # Fallback: Create basic tables if schema file not found
            conn.execute(text("""
                -- CUCM Tables
                CREATE TABLE IF NOT EXISTS cucm_phones (
                    id SERIAL PRIMARY KEY,
                    uuid UUID UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    product_name VARCHAR(100),
                    model VARCHAR(100),
                    protocol VARCHAR(50) DEFAULT 'SIP',
                    ip_address INET,
                    mac_address VARCHAR(17),
                    device_pool VARCHAR(100),
                    calling_search_space VARCHAR(100),
                    location VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'registered',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data JSONB
                );
                
                -- CMS Tables
                CREATE TABLE IF NOT EXISTS cms_cospaces (
                    id SERIAL PRIMARY KEY,
                    cospace_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    uri VARCHAR(255),
                    description TEXT,
                    passcode VARCHAR(100),
                    auto_attendant BOOLEAN DEFAULT FALSE,
                    owner_id VARCHAR(255),
                    owner_name VARCHAR(255),
                    access_level VARCHAR(50) DEFAULT 'PUBLIC',
                    max_participants INTEGER DEFAULT 50,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data JSONB
                );
                
                CREATE TABLE IF NOT EXISTS cms_calls (
                    id SERIAL PRIMARY KEY,
                    call_id VARCHAR(255) UNIQUE NOT NULL,
                    cospace_id VARCHAR(255) REFERENCES cms_cospaces(cospace_id),
                    cospace_name VARCHAR(255),
                    call_state VARCHAR(50) DEFAULT 'ACTIVE',
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER DEFAULT 0,
                    host_user_id VARCHAR(255),
                    host_user_name VARCHAR(255),
                    current_participants INTEGER DEFAULT 0,
                    max_participants INTEGER DEFAULT 50,
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data JSONB
                );
                
                -- Basic indexes
                CREATE INDEX IF NOT EXISTS idx_cucm_phones_uuid ON cucm_phones(uuid);
                CREATE INDEX IF NOT EXISTS idx_cucm_phones_name ON cucm_phones(name);
                CREATE INDEX IF NOT EXISTS idx_cms_cospaces_cospace_id ON cms_cospaces(cospace_id);
                CREATE INDEX IF NOT EXISTS idx_cms_calls_call_id ON cms_calls(call_id);
            """))
            logger.info("Created basic fallback database schemas")

@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    init_db()
    init_sync_components()
    logger.info("Census Clean started successfully")

# Health check
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check sync components
    sync_status = "not_initialized"
    if sync_manager:
        try:
            sync_status_info = sync_manager.get_sync_status()
            sync_status = f"connected_systems: {len(sync_status_info['connected_systems'])}"
        except Exception as e:
            sync_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "service": "Census Clean",
        "version": "2.0.0",
        "database": db_status,
        "sync": sync_status,
        "endpoints": {
            "devices": "/api/devices",
            "meetings": "/api/meetings",
            "users": "/api/users",
            "sync": "/api/sync",
            "middleware": "/api/middleware"
        }
    }

# Device endpoints
@app.get("/api/devices", response_model=List[Device])
async def get_devices(source: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all devices, optionally filtered by source"""
    query = "SELECT * FROM devices"
    params = {}
    if source:
        query += " WHERE source = :source"
        params["source"] = source
    
    result = db.execute(text(query), params)
    devices = []
    for row in result:
        devices.append(Device(
            id=row.id,
            name=row.name,
            ip_address=row.ip_address,
            mac_address=row.mac_address,
            device_type=row.device_type,
            status=row.status,
            source=row.source,
            raw_data=row.raw_data
        ))
    return devices

@app.post("/api/devices", response_model=Device)
async def create_device(device: Device, db: Session = Depends(get_db)):
    """Create or update a device"""
    try:
        # Insert or update device
        query = text("""
            INSERT INTO devices (name, ip_address, mac_address, device_type, status, source, raw_data)
            VALUES (:name, :ip_address, :mac_address, :device_type, :status, :source, :raw_data)
            ON CONFLICT (name, source) DO UPDATE SET
                ip_address = EXCLUDED.ip_address,
                mac_address = EXCLUDED.mac_address,
                device_type = EXCLUDED.device_type,
                status = EXCLUDED.status,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """)
        
        result = db.execute(query, {
            "name": device.name,
            "ip_address": device.ip_address,
            "mac_address": device.mac_address,
            "device_type": device.device_type,
            "status": device.status,
            "source": device.source,
            "raw_data": device.raw_data
        })
        db.commit()
        
        device.id = result.scalar()
        
        # Trigger middleware update
        if sync_middleware:
            sync_middleware.handle_update(
                "devices", device.name, 
                {}, device.dict(), device.source
            )
        
        return device
        
    except Exception as e:
        logger.error(f"Failed to create device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Meeting endpoints
@app.get("/api/meetings", response_model=List[Meeting])
async def get_meetings(source: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all meetings, optionally filtered by source"""
    query = "SELECT * FROM meetings"
    params = {}
    if source:
        query += " WHERE source = :source"
        params["source"] = source
    
    result = db.execute(text(query), params)
    meetings = []
    for row in result:
        meetings.append(Meeting(
            id=row.id,
            meeting_id=row.meeting_id,
            name=row.name,
            uri=row.uri,
            passcode=row.passcode,
            status=row.status,
            participants=row.participants,
            source=row.source,
            raw_data=row.raw_data
        ))
    return meetings

@app.post("/api/meetings", response_model=Meeting)
async def create_meeting(meeting: Meeting, db: Session = Depends(get_db)):
    """Create or update a meeting"""
    try:
        query = text("""
            INSERT INTO meetings (meeting_id, name, uri, passcode, status, participants, source, raw_data)
            VALUES (:meeting_id, :name, :uri, :passcode, :status, :participants, :source, :raw_data)
            ON CONFLICT (meeting_id, source) DO UPDATE SET
                name = EXCLUDED.name,
                uri = EXCLUDED.uri,
                passcode = EXCLUDED.passcode,
                status = EXCLUDED.status,
                participants = EXCLUDED.participants,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """)
        
        result = db.execute(query, {
            "meeting_id": meeting.meeting_id,
            "name": meeting.name,
            "uri": meeting.uri,
            "passcode": meeting.passcode,
            "status": meeting.status,
            "participants": meeting.participants,
            "source": meeting.source,
            "raw_data": meeting.raw_data
        })
        db.commit()
        
        meeting.id = result.scalar()
        
        # Trigger middleware update
        if sync_middleware:
            sync_middleware.handle_update(
                "meetings", meeting.meeting_id,
                {}, meeting.dict(), meeting.source
            )
        
        return meeting
        
    except Exception as e:
        logger.error(f"Failed to create meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User endpoints
@app.get("/api/users", response_model=List[User])
async def get_users(source: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all users, optionally filtered by source"""
    query = "SELECT * FROM users"
    params = {}
    if source:
        query += " WHERE source = :source"
        params["source"] = source
    
    result = db.execute(text(query), params)
    users = []
    for row in result:
        users.append(User(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            email=row.email,
            department=row.department,
            phone=row.phone,
            source=row.source,
            raw_data=row.raw_data
        ))
    return users

@app.post("/api/users", response_model=User)
async def create_user(user: User, db: Session = Depends(get_db)):
    """Create or update a user"""
    try:
        query = text("""
            INSERT INTO users (user_id, name, email, department, phone, source, raw_data)
            VALUES (:user_id, :name, :email, :department, :phone, :source, :raw_data)
            ON CONFLICT (user_id, source) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                department = EXCLUDED.department,
                phone = EXCLUDED.phone,
                raw_data = EXCLUDED.raw_data,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """)
        
        result = db.execute(query, {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "department": user.department,
            "phone": user.phone,
            "source": user.source,
            "raw_data": user.raw_data
        })
        db.commit()
        
        user.id = result.scalar()
        
        # Trigger middleware update
        if sync_middleware:
            sync_middleware.handle_update(
                "users", user.user_id,
                {}, user.dict(), user.source
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sync endpoints
@app.post("/api/sync")
async def trigger_sync(system: Optional[str] = None):
    """Trigger synchronization"""
    if not sync_manager:
        raise HTTPException(status_code=503, detail="Sync manager not initialized")
    
    try:
        if system:
            result = sync_manager.sync_system(system)
        else:
            result = sync_manager.full_sync()
        
        return result
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sync/status")
async def get_sync_status():
    """Get synchronization status"""
    if not sync_manager:
        raise HTTPException(status_code=503, detail="Sync manager not initialized")
    
    try:
        return sync_manager.get_sync_status()
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Middleware endpoints
@app.post("/api/middleware/update")
async def middleware_update(entity_type: str, entity_id: str, 
                          old_data: Dict[str, Any], new_data: Dict[str, Any],
                          source_system: str):
    """Handle middleware update"""
    if not sync_middleware:
        raise HTTPException(status_code=503, detail="Sync middleware not initialized")
    
    try:
        result = sync_middleware.handle_update(
            entity_type, entity_id, old_data, new_data, source_system
        )
        return result
        
    except Exception as e:
        logger.error(f"Middleware update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/middleware/create")
async def middleware_create(entity_type: str, entity_data: Dict[str, Any],
                           target_systems: Optional[List[str]] = None):
    """Create entity via middleware"""
    if not sync_middleware:
        raise HTTPException(status_code=503, detail="Sync middleware not initialized")
    
    try:
        result = sync_middleware.create_entity(entity_type, entity_data, target_systems)
        return result
        
    except Exception as e:
        logger.error(f"Middleware create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CUCM-specific endpoints
@app.get("/api/cucm/phones")
async def get_cucm_phones(status: Optional[str] = None, device_pool: Optional[str] = None, 
                         db: Session = Depends(get_db)):
    """Get CUCM phones with filtering"""
    query = "SELECT * FROM cucm_phones WHERE 1=1"
    params = {}
    if status:
        query += " AND status = :status"
        params["status"] = status
    if device_pool:
        query += " AND device_pool = :device_pool"
        params["device_pool"] = device_pool
    
    result = db.execute(text(query), params)
    phones = [dict(row._mapping) for row in result]
    return phones

@app.get("/api/cucm/phones/{phone_uuid}")
async def get_cucm_phone(phone_uuid: str, db: Session = Depends(get_db)):
    """Get specific CUCM phone by UUID"""
    result = db.execute(
        text("SELECT * FROM cucm_phones WHERE uuid = :uuid"),
        {"uuid": phone_uuid}
    )
    phone = result.fetchone()
    if not phone:
        raise HTTPException(status_code=404, detail="Phone not found")
    return dict(phone._mapping)

@app.get("/api/cucm/lines")
async def get_cucm_lines(pattern: Optional[str] = None, db: Session = Depends(get_db)):
    """Get CUCM lines"""
    query = "SELECT * FROM cucm_lines WHERE 1=1"
    params = {}
    if pattern:
        query += " AND pattern LIKE :pattern"
        params["pattern"] = f"%{pattern}%"
    
    result = db.execute(text(query), params)
    lines = [dict(row._mapping) for row in result]
    return lines

@app.get("/api/cucm/users")
async def get_cucm_users(department: Optional[str] = None, db: Session = Depends(get_db)):
    """Get CUCM users"""
    query = "SELECT * FROM cucm_users WHERE 1=1"
    params = {}
    if department:
        query += " AND department = :department"
        params["department"] = department
    
    result = db.execute(text(query), params)
    users = [dict(row._mapping) for row in result]
    return users

# CMS-specific endpoints
@app.get("/api/cms/cospaces")
async def get_cms_cospaces(access_level: Optional[str] = None, db: Session = Depends(get_db)):
    """Get CMS CoSpaces"""
    query = "SELECT * FROM cms_cospaces WHERE 1=1"
    params = {}
    if access_level:
        query += " AND access_level = :access_level"
        params["access_level"] = access_level
    
    result = db.execute(text(query), params)
    cospaces = [dict(row._mapping) for row in result]
    return cospaces

@app.get("/api/cms/cospaces/{cospace_id}")
async def get_cms_cospace(cospace_id: str, db: Session = Depends(get_db)):
    """Get specific CMS CoSpace"""
    result = db.execute(
        text("SELECT * FROM cms_cospaces WHERE cospace_id = :cospace_id"),
        {"cospace_id": cospace_id}
    )
    cospace = result.fetchone()
    if not cospace:
        raise HTTPException(status_code=404, detail="CoSpace not found")
    return dict(cospace._mapping)

@app.get("/api/cms/calls")
async def get_cms_calls(call_state: Optional[str] = None, db: Session = Depends(get_db)):
    """Get CMS calls"""
    query = "SELECT * FROM cms_calls WHERE 1=1"
    params = {}
    if call_state:
        query += " AND call_state = :call_state"
        params["call_state"] = call_state
    
    result = db.execute(text(query), params)
    calls = [dict(row._mapping) for row in result]
    return calls

@app.get("/api/cms/calls/{call_id}/participants")
async def get_cms_call_participants(call_id: str, db: Session = Depends(get_db)):
    """Get participants for a specific CMS call"""
    result = db.execute(
        text("SELECT * FROM cms_call_participants WHERE call_id = :call_id"),
        {"call_id": call_id}
    )
    participants = [dict(row._mapping) for row in result]
    return participants

# Database schema info
@app.get("/api/schema")
async def get_schema_info():
    """Get database schema information"""
    return {
        "cucm_tables": ["cucm_phones", "cucm_lines", "cucm_users"],
        "cms_tables": ["cms_cospaces", "cms_calls", "cms_call_participants"],
        "legacy_tables": ["devices", "meetings", "users"],
        "schema_file": "database_schemas.sql"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
