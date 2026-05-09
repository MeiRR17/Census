# Census Client SDK

ספרייה ייעודית לאפליקציות קצה לתקשור עם Census API.

## 📦 התקנה

```bash
npm install census-client-sdk
```

## 🚀 שימוש בסיסי

```javascript
import { CensusClient } from 'census-client-sdk';

const client = new CensusClient('http://localhost:8000');
```

## 📋 פונקציות מסוימות

### פעולות מכשירים
```javascript
// קבלת כל המכשירים
const devices = await client.getDevices();

// קבלת מכשירים ממקור ספציפי
const cucmDevices = await client.getDevices('cucm');

// יצירת מכשיר חדש
const device = await client.createDevice({
  name: 'SEP001122334455',
  ip_address: '192.168.1.100',
  device_type: 'Cisco 8841',
  source: 'census'
});

// עדכון מכשיר קיים
await client.updateDevice('SEP001122334455', {
  ip_address: '192.168.1.101',
  status: 'online'
});
```

### פעולות משתמשים
```javascript
// קבלת כל המשתמשים
const users = await client.getUsers();

// יצירת משתמש חדש
const user = await client.createUser({
  user_id: 'jdoe',
  name: 'John Doe',
  email: 'john@example.com',
  source: 'cucm'
});

// עדכון משתמש קיים
await client.updateUser('jdoe', {
  email: 'john.doe@example.com'
});
```

### פעולות ועידות
```javascript
// קבלת כל הוועידות
const meetings = await client.getMeetings();

// יצירת ועידה חדשה
const meeting = await client.createMeeting({
  meeting_id: 'CONF001',
  name: 'Test Conference',
  uri: 'conf001',
  passcode: '123456',
  source: 'cms'
});

// עדכון ועידה קיימת
await client.updateMeeting('CONF001', {
  passcode: '654321'
});
```

### פעולות סינכרון
```javascript
// הפעלת סינכרון מלא
await client.triggerFullSync();

// הפעלת סינכרון למערכת ספציפית
await client.triggerSync('cucm');

// קבלת סטטוס סינכרון
const status = await client.getSyncStatus();
```

## 🔧 פונקציות מתקדמות

### פעולות מכשירים מתקדמות
```javascript
// קבלת מכשירים מ-CUCM בלבד
const cucmPhones = await client.getCUCMDevices();

// קבלת מכשירים מ-CMS בלבד
const cmsDevices = await client.getCMSDevices();

// רישום טלפון חדש ב-CUCM
const phone = await client.registerPhone({
  name: 'SEP001122334455',
  ip_address: '192.168.1.100',
  mac_address: '00:11:22:33:44:55',
  model: 'Cisco 8841'
});
```

### פעולות ועידות מתקדמות
```javascript
// קבלת ועידות מ-CMS בלבד
const cmsMeetings = await client.getCMSMeetings();

// יצירת חדר ועידה חדש ב-CMS
const room = await client.createMeetingRoom({
  meeting_id: 'CONF001',
  name: 'Test Conference',
  passcode: '123456'
});
```

### פעולות משתמשים מתקדמות
```javascript
// קבלת משתמשים מ-CUCM בלבד
const cucmUsers = await client.getCUCMUsers();
```

## 🎯 דוגמאות מעשיות

### דוגמה 1: יצירת מכשיר וסינכרון
```javascript
import { CensusClient } from 'census-client-sdk';

async function addNewDevice() {
  const client = new CensusClient('http://localhost:8000');
  
  try {
    // 1. יצירת המכשיר ב-Census
    const device = await client.createDevice({
      name: 'SEP001122334455',
      ip_address: '192.168.1.100',
      mac_address: '00:11:22:33:44:55',
      device_type: 'Cisco 8841',
      status: 'registered',
      source: 'census'
    });
    
    console.log('Device created:', device);
    
    // 2. הפעלת סינכרון ל-CUCM כדי לוודא שהמכשיר מופץ
    await client.triggerSync('cucm');
    
    console.log('Sync triggered for CUCM');
    
  } catch (error) {
    console.error('Failed to add device:', error);
  }
}

addNewDevice();
```

### דוגמה 2: ניהול ועידות
```javascript
async function manageMeetings() {
  const client = new CensusClient('http://localhost:8000');
  
  try {
    // 1. קבלת כל הוועידות הפעילות
    const meetings = await client.getMeetings('cms');
    console.log('Active meetings:', meetings);
    
    // 2. יצירת ועידה חדשה
    const newMeeting = await client.createMeetingRoom({
      meeting_id: 'TEAM_SYNC_' + Date.now(),
      name: 'Team Sync Meeting',
      passcode: '123456'
    });
    
    console.log('New meeting created:', newMeeting);
    
    // 3. עדכון פרטי הוועידה
    await client.updateMeeting(newMeeting.meeting_id, {
      name: 'Updated Team Sync Meeting',
      passcode: '654321'
    });
    
    console.log('Meeting updated');
    
  } catch (error) {
    console.error('Failed to manage meetings:', error);
  }
}

manageMeetings();
```

### דוגמה 3: סקריפט סינכרון אוטומטי
```javascript
async function syncAllSystems() {
  const client = new CensusClient('http://localhost:8000');
  
  try {
    // 1. בדיקת סטטוס כל המערכות
    const status = await client.getSyncStatus();
    console.log('Current sync status:', status);
    
    // 2. הפעלת סינכרון מלא
    const result = await client.triggerFullSync();
    console.log('Full sync result:', result);
    
    // 3. המתנה לסיום הסינכרון
    setTimeout(async () => {
      const newStatus = await client.getSyncStatus();
      console.log('Updated sync status:', newStatus);
    }, 10000); // 10 שניות
    
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

syncAllSystems();
```

## 📝 הערות חשובות

- כל הפעולות מחזירות Promise - יש להשתמש ב-`await` או `.then()`
- במקרה של שגיאה, הפונקציות זורקות Exception
- כתובת ה-API היא `http://localhost:8000` כברירת מחדל
- כל השינויים מסתנכרנים אוטומטית למערכות הרלוונטיות

## 🔗 קישורים שימושיים

- [Census API Documentation](http://localhost:8000/docs)
- [Health Check](http://localhost:8000/health)
- [Sync Status](http://localhost:8000/api/sync/status)
