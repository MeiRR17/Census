"""
Simple Census MVP - Bridge between edge apps and Cisco/Oracle servers
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple configuration
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://census_user:census_password@localhost:5432/census_db")
    CUCM_HOST = os.getenv("CUCM_HOST", "")
    CUCM_USERNAME = os.getenv("CUCM_USERNAME", "")
    CUCM_PASSWORD = os.getenv("CUCM_PASSWORD", "")
    CMS_HOST = os.getenv("CMS_HOST", "")
    CMS_USERNAME = os.getenv("CMS_USERNAME", "")
    CMS_PASSWORD = os.getenv("CMS_PASSWORD", "")
    EXPRESSWAY_HOST = os.getenv("EXPRESSWAY_HOST", "")
    EXPRESSWAY_USERNAME = os.getenv("EXPRESSWAY_USERNAME", "")
    EXPRESSWAY_PASSWORD = os.getenv("EXPRESSWAY_PASSWORD", "")
    SBC_HOST = os.getenv("SBC_HOST", "")
    SBC_USERNAME = os.getenv("SBC_USERNAME", "")
    SBC_PASSWORD = os.getenv("SBC_PASSWORD", "")

# Database setup
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple data models
class Device(BaseModel):
    id: Optional[int] = None
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: str
    status: str = "unknown"
    source: str  # cucm, cms, etc.
    raw_data: Optional[Dict[str, Any]] = None

class Meeting(BaseModel):
    id: Optional[int] = None
    meeting_id: str
    name: str
    uri: Optional[str] = None
    passcode: Optional[str] = None
    status: str = "active"
    participants: int = 0
    source: str  # cms, meetingplace
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
    title="Census Simple MVP",
    description="Bridge between edge apps and Cisco/Oracle servers",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple database tables (will be created on first run)
def init_db():
    """Initialize simple database schema"""
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS meetings (
                id SERIAL PRIMARY KEY,
                meeting_id VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                uri VARCHAR(255),
                passcode VARCHAR(100),
                status VARCHAR(50) DEFAULT 'active',
                participants INTEGER DEFAULT 0,
                source VARCHAR(50) NOT NULL,
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                department VARCHAR(100),
                phone VARCHAR(50),
                source VARCHAR(50) NOT NULL,
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_devices_source ON devices(source);
            CREATE INDEX IF NOT EXISTS idx_meetings_source ON meetings(source);
            CREATE INDEX IF NOT EXISTS idx_users_source ON users(source);
        """))
        conn.commit()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Census Simple MVP started")

# Health check
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Check database
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "service": "Census Simple MVP",
        "database": db_status,
        "endpoints": {
            "devices": "/api/devices",
            "meetings": "/api/meetings", 
            "users": "/api/users",
            "sync": "/api/sync"
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
    query = text("""
        INSERT INTO devices (name, ip_address, mac_address, device_type, status, source, raw_data)
        VALUES (:name, :ip_address, :mac_address, :device_type, :status, :source, :raw_data)
        ON CONFLICT (name) DO UPDATE SET
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
    return device

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
    query = text("""
        INSERT INTO meetings (meeting_id, name, uri, passcode, status, participants, source, raw_data)
        VALUES (:meeting_id, :name, :uri, :passcode, :status, :participants, :source, :raw_data)
        ON CONFLICT (meeting_id) DO UPDATE SET
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
    return meeting

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
    query = text("""
        INSERT INTO users (user_id, name, email, department, phone, source, raw_data)
        VALUES (:user_id, :name, :email, :department, :phone, :source, :raw_data)
        ON CONFLICT (user_id) DO UPDATE SET
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
    return user

# Sync endpoint (placeholder for future implementation)
@app.post("/api/sync")
async def sync_data():
    """Sync data with external servers"""
    return {"status": "sync_started", "message": "Sync functionality will be implemented"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
