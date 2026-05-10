# Census - Bridge System for Cisco/Oracle Integration

Clean deployment-ready version for edge applications.

## 🚀 Quick Start

```bash
# 1. Setup environment
cp config/.env.example config/.env
# Edit config/.env with your server details

# 2. Install dependencies
pip install -r utils/requirements_clean.txt

# 3. Run the application
python main.py
```

## 📁 Project Structure

```
Census/
├── main.py                     # Main application entry point
├── api_routers.py             # ← API endpoints for CMS/CUCM control
├── models.py                  # ← SQLAlchemy database models
├── data_access.py             # ← Database operations
├── database_schemas.sql       # ← Complete table schemas
├── clients/                   # External system clients
├── sync/                      # Synchronization system
├── services/                  # ← Service layer (CMS service)
├── utils/                     # Utilities and SDK
│   ├── simple_sdk.py          # SDK for edge applications
│   └── requirements_clean.txt # Dependencies
└── config/                    # Configuration files
```

## 📖 API Endpoints

### **CMS (מלא):**
```python
GET    /api/cms/cospaces                    # רשימת CoSpaces
POST   /api/cms/cospaces                    # יצירת CoSpace
GET    /api/cms/cospaces/{id}               # פרטי CoSpace
PUT    /api/cms/cospaces/{id}/passcode     # עדכון סיסמה
DELETE /api/cms/cospaces/{id}               # מחיקת CoSpace

GET    /api/cms/calls/active                # שיחות פעילות בזמן אמת
GET    /api/cms/calls/{id}/participants     # משתתפים בשיחה

POST   /api/cms/calls/{id}/participants/{name}/mute    # השתקה
POST   /api/cms/calls/{id}/participants/{name}/unmute  # ביטול השתקה
DELETE /api/cms/calls/{id}/participants/{name}          # סילוק
```

### **CUCM (מלא):**
```python
GET    /api/cucm/phones       # רשימת טלפונים
POST   /api/cucm/phones       # יצירת טלפון
GET    /api/cucm/phones/{id}  # פרטי טלפון

GET    /api/cucm/lines        # רשימת שורות
POST   /api/cucm/lines        # יצירת שורה

GET    /api/cucm/users        # רשימת משתמשים
POST   /api/cucm/users        # יצירת משתמש
```

### **UCCX (מלא):**
```python
GET    /api/uccx/system/status    # סטטוס מערכת

GET    /api/uccx/agents          # רשימת נציגים
POST   /api/uccx/agents          # יצירת נציג
PUT    /api/uccx/agents/{id}     # עדכון נציג
DELETE /api/uccx/agents/{id}     # מחיקת נציג

GET    /api/uccx/teams           # רשימת צוותים
GET    /api/uccx/queues          # רשימת תורים (CSQs)
```

### **Legacy Endpoints:**
- **Health Check**: `/health`
- **Devices**: `/api/devices` (GET, POST)
- **Meetings**: `/api/meetings` (GET, POST)
- **Users**: `/api/users` (GET, POST)
- **Sync**: `/api/sync` (POST), `/api/sync/status` (GET)
- **Middleware**: `/api/middleware/update` (POST), `/api/middleware/create` (POST)

## 🔧 Edge Application Integration

Use the `utils/simple_sdk.py` to connect your edge applications to Census.

### **בסיסי:**
```python
from utils.simple_sdk import CensusSDK

# Initialize SDK
sdk = CensusSDK(base_url="http://localhost:8000")

# Get devices
devices = sdk.get_devices()

# Create a meeting
meeting = sdk.create_meeting({
    "meeting_id": "meeting-123",
    "name": "Team Meeting",
    "source": "edge_app"
})
```

### **CMS Operations (דרך Census):**
```python
# יצירת CoSpace
sdk.create_cms_cospace(
    name="Team Standup",
    uri="team-standup",
    passcode="123456"
)

# קבלת שיחות פעילות
calls = sdk.get_cms_active_calls()

# שליטה במשתתפים
sdk.mute_cms_participant(call_id="123", participant_name="John")
sdk.unmute_cms_participant(call_id="123", participant_name="John")
sdk.kick_cms_participant(call_id="123", participant_name="John")
```

### **CUCM Operations (דרך Census):**
```python
# יצירת טלפון
sdk.create_cucm_phone(
    name="SEP001122334455",
    model="Cisco 8841",
    device_pool="Default"
)

# יצירת שורה
sdk.create_cucm_line(pattern="1234", route_partition="Internal")

# יצירת משתמש
sdk.create_cucm_user(
    user_id="john.doe",
    first_name="John",
    last_name="Doe",
    department="Engineering"
)
```

### **UCCX Operations (דרך Census):**
```python
# יצירת נציג
sdk.create_uccx_agent(
    agent_id="agent001",
    first_name="David",
    last_name="Smith",
    extension="5001",
    team_id="sales_team"
)

# קבלת נציגים
agents = sdk.get_uccx_agents()

# עדכון נציג
sdk.update_uccx_agent(
    agent_id="agent001",
    extension="5002",
    status="READY"
)

# מחיקת נציג
sdk.delete_uccx_agent("agent001")

# קבלת צוותים
sdk.get_uccx_teams()

# קבלת תורים
sdk.get_uccx_queues()
```

## 🏗️ **ארכיטקטורה - Census כ-Proxy**

```
                    ┌─────────────────┐
                    │   CMS Server    │
אפליקציית קצה ──►   │ (Cisco Video)   │
                    └─────────────────┘
     │                    │
     │              ┌─────────────────┐
     │              │   CUCM Server   │
     └──────► Census│ (Cisco Voice)   │
            (Proxy)└─────────────────┘
     מדבר רק        │
     עם Census      │
                    └─────────────────┘
                    │   UCCX Server   │
                    │ (Contact Center)│
                    └─────────────────┘
```

### **איך זה עובד:**
1. **אפליקציית קצה** מדברת רק עם Census (דרך SDK)
2. **Census** מקבל את הבקשה ומפנה אותה לשרת המתאים (CMS/CUCM/UCCX)
3. **Census** שומר את התוצאה בדאטאבייס
4. **Census** מחזיר תשובה לאפליקציית הקצה

### **יתרונות:**
- ✅ אפליקציות קצה לא צריכות לדעת על CMS/CUCM/UCCX
- ✅ מיקוד כל הפעולות דרך נקודה אחת
- ✅ שמירת היסטוריה בדאטאבייס
- ✅ אבטחה - הרשאות רק ב-Census
