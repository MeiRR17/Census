# Census Architecture - Complete System Overview

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Edge Apps     │    │   Census API   │    │ External Systems│
│                 │    │                 │    │                 │
│ • Web Apps      │◄──►│ • FastAPI       │◄──►│ • CUCM          │
│ • Mobile Apps   │    │ • PostgreSQL    │    │ • CMS           │
│ • Desktop Apps  │    │ • Sync Engine   │    │ • MeetingPlace  │
│ • IoT Devices   │    │ • Middleware    │    │ • UCCX          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Data Flow

### 1. **Edge Apps → Census**
```python
# Edge app connects using simple SDK
from utils.simple_sdk import CensusSDK

sdk = CensusSDK(base_url="http://localhost:8000")

# Create meeting in Census
meeting = sdk.create_meeting({
    "meeting_id": "team-standup",
    "name": "Team Standup",
    "source": "edge_app"
})

# Census stores in PostgreSQL
# Middleware detects change and updates external systems
```

### 2. **Census → External Systems**
```python
# Census sync manager pulls data from external systems
sync_manager = SyncManager(systems_config, db_engine)

# Sync CMS calls → Census database
cms_client = CMSClient.create_from_env()
calls = cms_client.get_active_calls()

# Store in unified format
for call in calls:
    meeting = {
        'meeting_id': call['callId'],
        'name': f"Call {call['callId']}",
        'status': 'active',
        'source': 'cms'
    }
    # Store in database
```

### 3. **Bidirectional Sync**
```
Edge App creates meeting → Census stores → Middleware updates CMS
CMS call starts → Sync Engine detects → Database updates → Edge apps can query
```

## 📡 API Endpoints

### Core Data Endpoints
```
GET  /api/devices          # Get all devices
POST /api/devices          # Create/update device
GET  /api/meetings        # Get all meetings  
POST /api/meetings        # Create/update meeting
GET  /api/users           # Get all users
POST /api/users           # Create/update user
```

### Sync Endpoints
```
POST /api/sync            # Trigger manual sync
GET  /api/sync/status     # Get sync status
```

### Middleware Endpoints
```
POST /api/middleware/update   # Handle updates from edge apps
POST /api/middleware/create   # Create entities in external systems
```

## 🔧 Client Connections

### CMS Client (Full Featured)
```python
# Connect to Cisco Meeting Server
cms_client = CMSClient(
    base_url="https://cms.company.com:8443",
    username="admin",
    password="password"
)

# Full CMS operations
cospaces = cms_client.get_cospaces()
calls = cms_client.get_active_calls()
cms_client.mute_participant(call_id, "John Doe")
cms_client.kick_participant(call_id, "Jane Smith")
```

### MeetingPlace Client
```python
# Connect to MeetingPlace
mp_client = MeetingPlaceClient(
    host="meetingplace.company.com",
    username="admin", 
    password="password"
)

# Full MeetingPlace operations
meetings = mp_client.get_meetings()
users = mp_client.get_users()
mp_client.create_meeting("Team Meeting", "2024-01-01T10:00:00", 60)
```

## 🗄️ Database Schema

### Unified Tables
```sql
-- All devices from all systems
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ip_address INET,
    device_type VARCHAR(100),
    status VARCHAR(50),
    source VARCHAR(50) NOT NULL,  -- 'cms', 'cucm', 'meetingplace'
    raw_data JSONB,              -- Original system data
    UNIQUE(name, source)
);

-- All meetings/calls from all systems  
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    participants INTEGER,
    raw_data JSONB,
    UNIQUE(meeting_id, source)
);

-- All users from all systems
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    raw_data JSONB,
    UNIQUE(user_id, source)
);
```

## 🚀 Edge App Integration

### Simple SDK Usage
```python
# Install: pip install requests
from utils.simple_sdk import CensusSDK

# Initialize connection
sdk = CensusSDK(base_url="http://census-server:8000")

# Get data from all systems
devices = sdk.get_devices()           # From CUCM, CMS, etc.
meetings = sdk.get_meetings()        # From CMS, MeetingPlace, etc.
users = sdk.get_users()              # From all systems

# Filter by source
cms_devices = sdk.get_devices(source="cms")
cucm_users = sdk.get_users(source="cucm")

# Create new entities
sdk.create_meeting({
    "meeting_id": "daily-standup",
    "name": "Daily Standup",
    "source": "edge_app",
    "participants": 5
})

# This automatically:
# 1. Stores in PostgreSQL
# 2. Triggers middleware
# 3. Updates external systems (CMS, MeetingPlace)
```

## 🔀 Sync Engine Operation

### Automatic Sync
```python
# Runs every X minutes per system
class SyncManager:
    def sync_system(self, system_name):
        client = self.get_client(system_name)
        
        if system_name == "cms":
            # Sync active calls as meetings
            calls = client.get_active_calls()
            for call in calls:
                self.store_meeting(call, "cms")
        
        elif system_name == "cucm":
            # Sync phones as devices  
            phones = client.get_phones()
            for phone in phones:
                self.store_device(phone, "cucm")
```

### Middleware Updates
```python
# Handles updates FROM edge apps TO external systems
class SyncMiddleware:
    def handle_update(self, entity_type, entity_id, old_data, new_data, source):
        # Update all other systems
        for system in self.systems:
            if system != source:
                client = self.get_client(system)
                client.update_entity(entity_type, new_data)
```

## 🌐 Deployment Architecture

### Docker Compose
```yaml
services:
  census:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - CMS_URL=https://cms:8443
      - CUCM_HOST=cucm
    depends_on:
      - postgres
  
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=census_db
```

### External System Connections
```
Census Server ──► CUCM (AXL/SOAP)
              ├──► CMS (REST/XML) 
              ├──► MeetingPlace (SOAP)
              ├──► UCCX (REST)
              ├──► Expressway (REST)
              └──► SBC (REST)
```

## 📊 Monitoring & Health

### Health Check Endpoint
```
GET /health
{
  "status": "ok",
  "service": "Census",
  "database": "connected",
  "sync": "connected_systems: 3",
  "endpoints": {
    "devices": "/api/devices",
    "meetings": "/api/meetings", 
    "users": "/api/users"
  }
}
```

## 🔐 Security

### Authentication
- Environment variables for external system credentials
- Optional API key authentication for edge apps
- SSL/TLS encryption for all connections

### Authorization
- Role-based access control
- System-specific permissions
- Audit logging for all changes

---

## 🎯 Key Benefits

1. **Unified Interface**: Single API for all Cisco/Oracle systems
2. **Real-time Sync**: Automatic bidirectional synchronization  
3. **Edge App Ready**: Simple SDK for easy integration
4. **Scalable**: Docker-based deployment
5. **Reliable**: Robust error handling and retry logic
6. **Flexible**: Support for custom entities and workflows
