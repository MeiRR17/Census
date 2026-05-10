# Census - Central Hub Architecture

## 🎯 **The Core Concept: Census as Central Hub**

**Census is NOT a client that connects to external systems.**
**Census IS the central server that ALL edge apps connect to.**

```
┌─────────────────────────────────────────────────────────────┐
│                    CENSUS CENTRAL HUB                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ PostgreSQL  │  │ FastAPI     │  │ Sync Engine │   │
│  │ Database    │  │ Server      │  │             │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Edge App 1  │    │ Edge App 2  │    │ Edge App N  │
│ (Web/Mobile)│    │ (Desktop)   │    │ (IoT)       │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔄 **Correct Data Flow**

### 1. **Edge Apps → Census (PRIMARY FLOW)**
```python
# Edge app connects to Census
from utils.simple_sdk import CensusSDK

sdk = CensusSDK(base_url="http://census-server:8000")

# Edge app creates/reads data THROUGH Census
meeting = sdk.create_meeting({
    "meeting_id": "team-standup",
    "name": "Team Standup",
    "source": "edge_app_1"
})

devices = sdk.get_devices()  # Gets data from ALL edge apps
```

### 2. **Census Manages All Data**
```python
# Census stores everything in unified tables
class CensusManager:
    def create_meeting(self, meeting_data):
        # Store in PostgreSQL
        meeting_id = self.db.insert_meeting(meeting_data)
        
        # Notify other edge apps via WebSocket/Events
        self.event_manager.broadcast("meeting_created", meeting_data)
        
        return meeting_id
```

### 3. **Optional: External System Integration (FUTURE)**
```python
# ONLY if needed, Census can ALSO connect to external systems
# But this is ADDITIONAL functionality, not the main purpose

class ExternalSync:
    def sync_to_cucm(self, data):
        # Optional: Push data to CUCM
        pass
    
    def sync_from_cms(self, data):
        # Optional: Pull data from CMS
        pass
```

## 🏗️ **Simplified Client Architecture**

### The "clients" are actually FOR edge apps to connect TO Census:
```python
# clients/cms_client.py - For edge apps to connect to Census
class CensusClient:
    def __init__(self, census_url):
        self.base_url = census_url
    
    def get_meetings(self):
        # Get meetings FROM Census database
        response = requests.get(f"{self.base_url}/api/meetings")
        return response.json()
    
    def create_meeting(self, meeting_data):
        # Create meeting IN Census database
        response = requests.post(f"{self.base_url}/api/meetings", json=meeting_data)
        return response.json()
```

### NOT for connecting TO external CMS servers!

## 📊 **Unified Database Schema**

```sql
-- All data from ALL edge apps goes here
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    source_app VARCHAR(100) NOT NULL,  -- Which edge app created this
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(meeting_id, source_app)
);

CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    source_app VARCHAR(100) NOT NULL,  -- Which edge app owns this
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, source_app)
);
```

## 🔧 **Edge App Integration**

### Simple SDK for Edge Apps:
```python
# utils/simple_sdk.py - THE ACTUAL SDK for edge apps
class CensusSDK:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_meetings(self):
        """Get meetings from Census central database"""
        response = requests.get(f"{self.base_url}/api/meetings")
        return response.json()
    
    def create_meeting(self, meeting_data):
        """Create meeting in Census central database"""
        meeting_data["source_app"] = self.app_name
        response = requests.post(f"{self.base_url}/api/meetings", json=meeting_data)
        return response.json()
    
    def get_devices(self, source_app=None):
        """Get devices from Census central database"""
        url = f"{self.base_url}/api/devices"
        if source_app:
            url += f"?source_app={source_app}"
        response = requests.get(url)
        return response.json()
```

## 🚀 **Deployment**

### Single Central Server:
```yaml
# docker-compose.yml
services:
  census:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://census:password@postgres:5432/census
    depends_on:
      - postgres
  
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=census
      - POSTGRES_USER=census
      - POSTGRES_PASSWORD=password
```

### Edge Apps Connect to Census:
```python
# Edge app configuration
CENSUS_URL = "http://census-server:8000"
MY_APP_NAME = "meeting_scheduler"

sdk = CensusSDK(base_url=CENSUS_URL)
sdk.app_name = MY_APP_NAME

# All operations go through Census
meetings = sdk.get_meetings()
new_meeting = sdk.create_meeting({...})
```

## 📡 **API Endpoints (Central Hub)**

### For Edge Apps:
```
GET  /api/meetings           # Get all meetings from all edge apps
POST /api/meetings           # Create meeting (stores which app created it)
GET  /api/devices            # Get all devices from all edge apps
POST /api/devices            # Create device (stores which app owns it)
GET  /api/users              # Get all users from all edge apps
POST /api/users              # Create user (stores which app created it)
```

### Real-time Events:
```
WS   /ws/events              # WebSocket for real-time updates
     - meeting_created
     - device_updated
     - user_deleted
```

## 🎯 **Key Benefits of Central Hub Architecture**

1. **Single Source of Truth**: All data in one place
2. **Easy Edge App Development**: Simple SDK, no complex integrations
3. **Real-time Sync**: All edge apps see updates immediately
4. **Scalable**: Add unlimited edge apps
5. **Unified Data**: Consistent format across all apps
6. **No External Dependencies**: Works standalone

## 🔍 **What This Means**

- **Census = Central Database + API Server**
- **Edge Apps = Connect TO Census**
- **Clients = Libraries for edge apps to connect TO Census**
- **External Systems = Optional future enhancement**

**The main goal is NOT to connect to CUCM/CMS.**
**The main goal is to be the central hub for ALL edge apps!**
