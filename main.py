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
    """Initialize database schema"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS devices (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                ip_address INET,
                mac_address VARCHAR(17),
                device_type VARCHAR(100),
                status VARCHAR(50) DEFAULT 'unknown',
                source VARCHAR(50) NOT NULL,
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, source)
            );
            
            CREATE TABLE IF NOT EXISTS meetings (
                id SERIAL PRIMARY KEY,
                meeting_id VARCHAR(255) NOT NULL,
                source VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                uri VARCHAR(255),
                passcode VARCHAR(100),
                status VARCHAR(50) DEFAULT 'active',
                participants INTEGER DEFAULT 0,
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meeting_id, source)
            );
            
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                source VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                department VARCHAR(100),
                phone VARCHAR(50),
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, source)
            );
            
            CREATE INDEX IF NOT EXISTS idx_devices_source ON devices(source);
            CREATE INDEX IF NOT EXISTS idx_meetings_source ON meetings(source);
            CREATE INDEX IF NOT EXISTS idx_users_source ON users(source);
            CREATE INDEX IF NOT EXISTS idx_devices_name ON devices(name);
            CREATE INDEX IF NOT EXISTS idx_meetings_id ON meetings(meeting_id);
            CREATE INDEX IF NOT EXISTS idx_users_userid ON users(user_id);
        """))
        conn.commit()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
