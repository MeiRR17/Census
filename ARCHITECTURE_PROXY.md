# Census Proxy Architecture - Complete Control Through Census

## 🎯 **The Architecture You Wanted**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Edge App      │────►│     Census      │────►│   CMS Server    │
│   (Your App)    │     │   (Proxy Layer) │     │  (Cisco Video)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   CUCM Server   │
                        │  (Cisco Voice)  │
                        └─────────────────┘
```

## 🔄 **How It Works**

### **1. Edge App ONLY Talks to Census**
```python
from utils.simple_sdk import CensusSDK

sdk = CensusSDK("http://census-server:8000")

# Create CoSpace through Census → CMS
sdk.create_cms_cospace(
    name="Team Meeting",
    uri="team-meeting",
    passcode="123456"
)

# Mute participant through Census → CMS
sdk.mute_cms_participant(
    call_id="call-123",
    participant_name="John Doe"
)

# Create phone through Census → CUCM
sdk.create_cucm_phone(
    name="SEP001122334455",
    model="Cisco 8841"
)
```

### **2. Census Proxies to CMS/CUCM**
```python
# Census endpoint receives request
@app.post("/api/cms/cospaces")
async def create_cospace(request):
    # 1. Validate request
    # 2. Connect to actual CMS server
    cms = CMS.create_from_env()  # Connects to CMS_HOST:CMS_PORT
    
    # 3. Forward request to CMS
    result = cms.create_cospace(
        name=request.name,
        uri=request.uri,
        passcode=request.passcode
    )
    
    # 4. Save to database
    save_cms_cospace(db, result)
    
    # 5. Return result to edge app
    return {"success": True, "cms_response": result}
```

### **3. All Client Functions Are Exposed as Endpoints**

| Client Function | Census Endpoint | SDK Method |
|-----------------|-----------------|------------|
| `create_cospace()` | `POST /api/cms/cospaces` | `sdk.create_cms_cospace()` |
| `delete_cospace()` | `DELETE /api/cms/cospaces/{id}` | `sdk.delete_cms_cospace()` |
| `update_passcode()` | `PUT /api/cms/cospaces/{id}/passcode` | `sdk.update_cospace_passcode()` |
| `get_active_calls()` | `GET /api/cms/calls/active` | `sdk.get_cms_active_calls()` |
| `mute_participant()` | `POST /api/cms/calls/{id}/participants/{name}/mute` | `sdk.mute_cms_participant()` |
| `unmute_participant()` | `POST /api/cms/calls/{id}/participants/{name}/unmute` | `sdk.unmute_cms_participant()` |
| `kick_participant()` | `DELETE /api/cms/calls/{id}/participants/{name}` | `sdk.kick_cms_participant()` |
| `create_phone()` | `POST /api/cucm/phones` | `sdk.create_cucm_phone()` |
| `create_line()` | `POST /api/cucm/lines` | `sdk.create_cucm_line()` |
| `create_user()` | `POST /api/cucm/users` | `sdk.create_cucm_user()` |

## 📡 **Complete API Reference**

### **CMS Endpoints**
```
GET    /api/cms/cospaces                    # List all CoSpaces
POST   /api/cms/cospaces                    # Create CoSpace
GET    /api/cms/cospaces/{id}               # Get CoSpace details
PUT    /api/cms/cospaces/{id}/passcode     # Update passcode
DELETE /api/cms/cospaces/{id}               # Delete CoSpace

GET    /api/cms/calls                       # List calls from DB
GET    /api/cms/calls/active                # Get active calls (real-time)
GET    /api/cms/calls/{id}                  # Get call details
GET    /api/cms/calls/{id}/participants     # Get participants

POST   /api/cms/calls/{id}/participants/{name}/mute    # Mute
POST   /api/cms/calls/{id}/participants/{name}/unmute  # Unmute
DELETE /api/cms/calls/{id}/participants/{name}        # Kick

GET    /api/cms/system/status               # CMS connection status
```

### **CUCM Endpoints**
```
GET    /api/cucm/phones                     # List phones
POST   /api/cucm/phones                     # Create phone
GET    /api/cucm/phones/{uuid}              # Get phone details

GET    /api/cucm/lines                      # List lines
POST   /api/cucm/lines                      # Create line
GET    /api/cucm/lines/{uuid}               # Get line details

GET    /api/cucm/users                      # List users
POST   /api/cucm/users                      # Create user
GET    /api/cucm/users/{id}                 # Get user details

GET    /api/cucm/system/status              # CUCM connection status
```

### **Unified Endpoints**
```
GET    /api/unified/meetings                # All meetings (CMS + others)
GET    /api/unified/devices                 # All devices (CUCM + others)
GET    /api/unified/users                   # All users (all systems)
```

## 🛠 **Files Structure**

```
Census/
├── api_routers.py              # ← All endpoints defined here
│   ├── cms_router              # CMS control endpoints
│   ├── cucm_router             # CUCM control endpoints
│   └── unified_router          # Combined view endpoints
│
├── services/
│   └── cms_service.py          # ← Actual CMS client functions
│       ├── CMSService          # Full CMS control class
│       └── CMS                 # Alternative CMS client
│
├── clients/
│   ├── cms_client.py           # ← CMS client for edge apps
│   └── cucm_client.py          # ← CUCM client for edge apps
│
├── utils/
│   └── simple_sdk.py           # ← SDK with all proxy methods
│       └── CensusSDK
│           ├── create_cms_cospace()
│           ├── mute_cms_participant()
│           ├── create_cucm_phone()
│           └── ... all client functions
│
├── data_access.py              # ← Database operations
│   ├── save_cms_cospace()
│   ├── save_cms_call()
│   ├── save_cucm_phone()
│   └── ...
│
├── models.py                   # ← SQLAlchemy models
│   ├── CMSCoSpace
│   ├── CMSCall
│   ├── CMSCallParticipant
│   ├── CUCMPhone
│   ├── CUCMLine
│   └── CUCMUser
│
└── database_schemas.sql        # ← Full table schemas
```

## 💡 **Usage Examples**

### **Creating a Meeting Room (CMS)**
```python
from utils.simple_sdk import CensusSDK

sdk = CensusSDK("http://census-server:8000")

# Edge app creates meeting through Census
result = sdk.create_cms_cospace(
    name="Engineering Standup",
    uri="eng-standup",
    passcode="123456",
    max_participants=50
)

print(f"Created: {result}")
# Output: Census → CMS → Database → Response
```

### **Controlling a Call (CMS)**
```python
# Get active calls
calls = sdk.get_cms_active_calls()

if calls['active_calls']:
    call_id = calls['active_calls'][0]['callId']
    
    # Get participants
    participants = sdk.get_cms_call_participants(call_id)
    
    # Mute first participant
    sdk.mute_cms_participant(
        call_id=call_id,
        participant_name=participants['participants'][0]['name']
    )
```

### **Provisioning a Phone (CUCM)**
```python
# Create new phone
phone = sdk.create_cucm_phone(
    name="SEP001122334455",
    description="Conference Room A",
    model="Cisco 8841",
    device_pool="Default",
    protocol="SIP"
)

# Create line for phone
line = sdk.create_cucm_line(
    pattern="1234",
    route_partition="Internal",
    description="Conf Room A Line"
)

# Create user
user = sdk.create_cucm_user(
    user_id="room.a",
    first_name="Conference",
    last_name="Room A",
    telephone_number="1234"
)
```

## 🔐 **Benefits of This Architecture**

1. **Edge Apps Know Nothing About CMS/CUCM**
   - Only need Census URL
   - No CMS/CUCM credentials needed
   - Simple HTTP calls

2. **Centralized Control**
   - All operations go through Census
   - Audit logging in one place
   - Unified error handling

3. **Database Persistence**
   - Every operation saved to DB
   - Historical tracking
   - Data analysis possible

4. **Security**
   - Credentials only in Census
   - Edge apps use API keys (optional)
   - No direct server access

5. **Flexibility**
   - Can swap CMS/CUCM servers
   - Edge apps don't change
   - Easy to add new systems

## 🚀 **Quick Start**

### **1. Configure Environment**
```bash
# .env file
CMS_HOST=192.168.1.20
CMS_USERNAME=admin
CMS_PASSWORD=admin123
CMS_PORT=8443

CUCM_HOST=192.168.1.10
CUCM_USERNAME=administrator
CUCM_PASSWORD=cisco123
CUCM_PORT=8443
```

### **2. Start Census**
```bash
docker-compose up
```

### **3. Use SDK from Edge App**
```python
from utils.simple_sdk import CensusSDK

sdk = CensusSDK("http://census-server:8000")

# All CMS/CUCM operations available
# through simple Census API calls!
```

## ✅ **Summary**

**What You Wanted:**
- ✅ All client functions exposed as Census endpoints
- ✅ Edge apps talk ONLY to Census
- ✅ Census proxies to CMS/CUCM
- ✅ Database stores everything
- ✅ Simple SDK for edge apps

**Result:** Complete proxy architecture where Census is the single control point for all Cisco systems!
