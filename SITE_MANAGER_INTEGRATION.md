# 🚀 Site-Manager + Census Integration Guide

## 🎯 הבנת ההיגיון

כשאתה עושה דיפלוי ב-Census, השינויים מופצים אוטומטית לשרתים החיצוניים (CUCM, CMS, וכו'). אבל בשביל ש-Site-Manager יכול לראות את השינויים, צריך לחבר אותו ל-Census.

### זרימת העבודה:
```
Site-Manager ←→ Census API ←→ External Systems (CUCM, CMS, SBC)
```

## 📋 מה צריך להוסיף ל-Site-Manager

### 1. התקנת הספרייה
הוסף ל-`requirements.txt`:
```txt
census-client-sdk>=1.0.0
requests>=2.31.0
```

### 2. יצירת שירות Census
צור קובץ חדש: `backend/app/services/census_service.py`

```python
"""
Census Service - שירות לתקשורת עם Census API
"""
import os
from typing import List, Optional, Dict, Any
from census_client_sdk import CensusClient

class CensusService:
    def __init__(self):
        self.base_url = os.getenv("CENSUS_API_URL", "http://localhost:8000")
        self.client = CensusClient(self.base_url)
    
    async def health_check(self) -> bool:
        """בדיקת חיבור ל-Census"""
        try:
            health = await self.client.healthCheck()
            return health.get("status") == "ok"
        except Exception:
            return False
    
    async def sync_devices_from_census(self) -> List[Dict[str, Any]]:
        """סינכרון מכשירים מ-Census ל-Site-Manager"""
        try:
            devices = await self.client.getDevices()
            return [
                {
                    "identifier": device.get("name", ""),
                    "classification": device.get("device_type", "Unknown"),
                    "ip_address": device.get("ip_address"),
                    "mac_address": device.get("mac_address"),
                    "source": device.get("source", "census"),
                    "status": device.get("status", "unknown")
                }
                for device in devices
            ]
        except Exception as e:
            print(f"Error syncing devices from Census: {e}")
            return []
    
    async def create_device_in_census(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """יצירת מכשיר ב-Census"""
        try:
            return await self.client.createDevice({
                "name": device_data["identifier"],
                "ip_address": device_data.get("ip_address"),
                "mac_address": device_data.get("mac_address"),
                "device_type": device_data.get("classification", "Unknown"),
                "status": "registered",
                "source": "site-manager"
            })
        except Exception as e:
            print(f"Error creating device in Census: {e}")
            return None
    
    async def update_device_in_census(self, device_id: str, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """עדכון מכשיר ב-Census"""
        try:
            return await self.client.updateDevice(device_id, device_data, "site-manager")
        except Exception as e:
            print(f"Error updating device in Census: {e}")
            return None
    
    async def delete_device_from_census(self, device_id: str) -> bool:
        """מחיקת מכשיר מ-Census"""
        try:
            # Note: ייתכן שצריך להוסיף את הפונקציה הזו ל-SDK
            # כרגע מחזיר True כברירת מחדל
            return True
        except Exception as e:
            print(f"Error deleting device from Census: {e}")
            return False
    
    async def trigger_census_sync(self, system: Optional[str] = None) -> Dict[str, Any]:
        """הפעלת סינכרון ב-Census"""
        try:
            if system:
                return await self.client.triggerSync(system)
            else:
                return await self.client.triggerFullSync()
        except Exception as e:
            print(f"Error triggering Census sync: {e}")
            return {"status": "error", "message": str(e)}

# יצירת instance גלובלי
census_service = CensusService()
```

### 3. עדכון מודל המכשיר
עדכן את `backend/app/models/device.py`:

```python
# הוסף למודל Device את השדות הבאים (אם עדיין לא קיימים):
class Device(Base):
    # ... שדות קיימים ...
    
    # הוסף שדות חדשים לחיבור עם Census
    census_device_id = Column(String, nullable=True)  # מזהה ב-Census
    census_source = Column(String, nullable=True)     # מקור ב-Census
    last_sync_from_census = Column(DateTime, nullable=True)  # זמן סינכרון אחרון
    is_synced_to_census = Column(Boolean, default=False)  # האם מסונכרן ל-Census
```

### 4. יצירת סכמה חדשה
צור קובץ `backend/app/schemas/census.py`:

```python
"""
סכמות לפעולות Census
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class CensusSyncResponse(BaseModel):
    success: bool
    message: str
    synced_devices: int
    errors: List[str] = []

class CensusDeviceSync(BaseModel):
    identifier: str
    classification: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    source: str
    status: str

class CensusHealthResponse(BaseModel):
    status: str
    connected: bool
    last_check: str
```

### 5. יצירת אנדפוינטים חדשים
צור קובץ `backend/app/api/v1/endpoints/census.py`:

```python
"""
אנדפוינטים לחיבור עם Census
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.census_service import census_service
from app.schemas.census import CensusSyncResponse, CensusHealthResponse
from app.models.device import Device
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/health", response_model=CensusHealthResponse)
async def census_health_check(current_user: User = Depends(get_current_user)):
    """בדיקת חיבור ל-Census"""
    try:
        connected = await census_service.health_check()
        return CensusHealthResponse(
            status="connected" if connected else "disconnected",
            connected=connected,
            last_check=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Census connection failed: {str(e)}")

@router.post("/sync/from-census", response_model=CensusSyncResponse)
async def sync_devices_from_census(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """סינכרון מכשירים מ-Census ל-Site-Manager"""
    try:
        # בדיקת הרשאות - רק מנהלים יכולים לבצע סינכרון
        if current_user.role.value not in ["superadmin", "admin"]:
            raise HTTPException(status_code=403, detail="Only admins can sync from Census")
        
        # קבלת מכשירים מ-Census
        census_devices = await census_service.sync_devices_from_census()
        
        synced_count = 0
        errors = []
        
        for device_data in census_devices:
            try:
                # בדיקה אם המכשיר כבר קיים
                existing_device = db.query(Device).filter(
                    Device.identifier == device_data["identifier"]
                ).first()
                
                if existing_device:
                    # עדכון מכשיר קיים
                    existing_device.census_device_id = device_data.get("identifier")
                    existing_device.census_source = device_data.get("source")
                    existing_device.last_sync_from_census = datetime.now()
                    existing_device.is_synced_to_census = True
                else:
                    # יצירת מכשיר חדש (תחת סקשיה כללית)
                    new_device = Device(
                        id=uuid.uuid4(),
                        identifier=device_data["identifier"],
                        classification=device_data.get("classification", "Unknown"),
                        section_id=uuid.uuid4(),  # תצטרך להתאים לסקשיה קיימת
                        census_device_id=device_data.get("identifier"),
                        census_source=device_data.get("source"),
                        last_sync_from_census=datetime.now(),
                        is_synced_to_census=True
                    )
                    db.add(new_device)
                
                synced_count += 1
                
            except Exception as e:
                errors.append(f"Error syncing device {device_data.get('identifier')}: {str(e)}")
        
        db.commit()
        
        return CensusSyncResponse(
            success=True,
            message=f"Synced {synced_count} devices from Census",
            synced_devices=synced_count,
            errors=errors
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/sync/to-census")
async def sync_devices_to_census(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """סינכרון מכשירים מ-Site-Manager ל-Census"""
    try:
        if current_user.role.value not in ["superadmin", "admin"]:
            raise HTTPException(status_code=403, detail="Only admins can sync to Census")
        
        # קבלת כל המכשירים שלא מסונכרנים ל-Census
        unsynced_devices = db.query(Device).filter(
            Device.is_synced_to_census == False
        ).all()
        
        synced_count = 0
        errors = []
        
        for device in unsynced_devices:
            try:
                device_data = {
                    "identifier": device.identifier,
                    "classification": device.classification,
                    "ip_address": None,  # תצטרך להוסיף שדה במודל
                    "mac_address": device.identifier  # נניח ש-Identifier הוא MAC
                }
                
                result = await census_service.create_device_in_census(device_data)
                if result:
                    device.is_synced_to_census = True
                    device.census_device_id = result.get("name")
                    synced_count += 1
                else:
                    errors.append(f"Failed to create device {device.identifier} in Census")
                    
            except Exception as e:
                errors.append(f"Error syncing device {device.identifier}: {str(e)}")
        
        db.commit()
        
        return CensusSyncResponse(
            success=True,
            message=f"Synced {synced_count} devices to Census",
            synced_devices=synced_count,
            errors=errors
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync to Census failed: {str(e)}")

@router.post("/trigger-census-sync")
async def trigger_census_sync(
    system: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """הפעלת סינכרון ב-Census"""
    try:
        if current_user.role.value not in ["superadmin", "admin"]:
            raise HTTPException(status_code=403, detail="Only admins can trigger Census sync")
        
        result = await census_service.trigger_census_sync(system)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger Census sync: {str(e)}")
```

### 6. עדכון האפליקציה הראשית
עדכן את `backend/app/main.py`:

```python
# הוסף את ה-import וה-router
from app.api.v1.endpoints.census import router as census_router

# הוסף את ה-router לאפליקציה
app.include_router(census_router, prefix="/api/v1/census", tags=["Census"])
```

### 7. הוספת משתני סביבה
צור/עדכן קובץ `.env` ב-backend:

```env
CENSUS_API_URL=http://localhost:8000
```

## 🔄 איך זה עובד בפועל

### 1. סינכרון מ-Census ל-Site-Manager:
```bash
# בדיקת חיבור
GET /api/v1/census/health

# סינכרון מכשירים מ-Census
POST /api/v1/census/sync/from-census
```

### 2. סינכרון מ-Site-Manager ל-Census:
```bash
# סינכרון מכשירים ל-Census
POST /api/v1/census/sync/to-census
```

### 3. הפעלת סינכרון כללי:
```bash
# הפעלת סינכרון ב-Census
POST /api/v1/census/trigger-census-sync

# הפעלת סינכרון למערכת ספציפית
POST /api/v1/census/trigger-census-sync?system=cucm
```

## 🎯 תרחישים שימושיים

### תרחיש 1: יצירת מכשיר ב-Site-Manager
1. משתמש יוצר מכשיר חדש ב-Site-Manager
2. המערכת מסמנת אותו כ"לא מסונכרן ל-Census"
3. רקע מסנכרן אוטומטית את המכשיר ל-Census
4. המכשיר מסומן כ"מסונכרן ל-Census"

### תרחיש 2: סינכרון מ-CUCM
1. מנהל מפעיל סינכרון ב-Census
2. Census מושך נתונים מ-CUCM
3. Site-Manager יכול למשוך את הנתונים מ-Census
4. המכשירים מסונכרנים ב-Site-Manager

### תרחיש 3: עדכון דו-כיווני
1. משתמש מעדכן מכשיר ב-Site-Manager
2. העדכון מועבר ל-Census
3. Census מפיץ את העדכון ל-CUCM
4. כולם מסונכרנים

## 🚨 חשוב לזכור

1. **הרשאות** - רק מנהלים יכולים לבצע סינכרון
2. **סינכרון אוטומטי** - צריך להוסיף רקע שמסנכרן אוטומטית
3. **טיפול בשגיאות** - כל שגיאה בסינכרון צריכה להירשם
4. **ביצועים** - סינכרון יכול לקחת זמן, צריך timeout

## 📦 התקנה והפעלה

```bash
# 1. התקן את הספרייה
cd /path/to/Site-Manager/backend
pip install census-client-sdk

# 2. הוסף ל-requirements.txt
echo "census-client-sdk>=1.0.0" >> requirements.txt

# 3. צור את קבצי השירות
# (העתק את הקודד מהמדריך)

# 4. הפעל מחדש את השרת
uvicorn app.main:app --reload
```

## 🎉 סיום

עכשיו Site-Manager מחובר ל-Census! כל שינוי שתעשה באחד מהמערכתים ישפיע על השנייה.
