/**
 * דוגמאות בסיסיות לשימוש ב-Census Client SDK
 */

// ייבוא הספרייה
const { CensusClient } = require('../dist/index.js');

// יצירת לקוח
const client = new CensusClient('http://localhost:8000');

// דוגמה 1: קבלת כל המכשירים
async function getAllDevices() {
  try {
    const devices = await client.getDevices();
    console.log('כל המכשירים:', devices);
    return devices;
  } catch (error) {
    console.error('שגיאה בקבלת מכשירים:', error.message);
  }
}

// דוגמה 2: יצירת מכשיר חדש
async function addNewDevice() {
  try {
    const device = await client.createDevice({
      name: 'SEP001122334455',
      ip_address: '192.168.1.100',
      mac_address: '00:11:22:33:44:55',
      device_type: 'Cisco 8841',
      status: 'online',
      source: 'census'
    });
    
    console.log('מכשיר נוצר בהצלחה:', device);
    return device;
  } catch (error) {
    console.error('שגיאה ביצירת מכשיר:', error.message);
  }
}

// דוגמה 3: עדכון מכשיר קיים
async function updateDevice() {
  try {
    const updatedDevice = await client.updateDevice(
      'SEP001122334455', 
      { 
        ip_address: '192.168.1.101',
        status: 'offline' 
      },
      'census'
    );
    
    console.log('מכשיר עודכן בהצלחה:', updatedDevice);
    return updatedDevice;
  } catch (error) {
    console.error('שגיאה בעדכון מכשיר:', error.message);
  }
}

// דוגמה 4: קבלת מכשירים ממקור ספציפי
async function getCUCMDevices() {
  try {
    const cucmDevices = await client.getCUCMDevices();
    console.log('מכשירי CUCM:', cucmDevices);
    return cucmDevices;
  } catch (error) {
    console.error('שגיאה בקבלת מכשירי CUCM:', error.message);
  }
}

// דוגמה 5: רישום טלפון ב-CUCM
async function registerPhone() {
  try {
    const phone = await client.registerPhone({
      name: 'SEP001122334455',
      ip_address: '192.168.1.100',
      mac_address: '00:11:22:33:44:55',
      model: 'Cisco 8841'
    });
    
    console.log('טלפון נרשם בהצלחה:', phone);
    return phone;
  } catch (error) {
    console.error('שגיאה ברישום טלפון:', error.message);
  }
}

// דוגמה 6: ניהול משתמשים
async function manageUsers() {
  try {
    // קבלת כל המשתמשים
    const users = await client.getUsers();
    console.log('כל המשתמשים:', users);
    
    // יצירת משתמש חדש
    const newUser = await client.createUser({
      user_id: 'jdoe',
      name: 'John Doe',
      email: 'john@example.com',
      source: 'cucm'
    });
    
    console.log('משתמש חדש נוצר:', newUser);
    
    // קבלת משתמשים מ-CUCM בלבד
    const cucmUsers = await client.getCUCMUsers();
    console.log('משתמשי CUCM:', cucmUsers);
    
  } catch (error) {
    console.error('שגיאה בניהול משתמשים:', error.message);
  }
}

// דוגמה 7: ניהול ועידות
async function manageMeetings() {
  try {
    // קבלת כל הוועידות
    const meetings = await client.getMeetings();
    console.log('כל הוועידות:', meetings);
    
    // יצירת ועידה חדשה
    const newMeeting = await client.createMeetingRoom({
      meeting_id: 'CONF001',
      name: 'Test Conference',
      passcode: '123456'
    });
    
    console.log('ועידה חדשה נוצרה:', newMeeting);
    
    // קבלת ועידות מ-CMS בלבד
    const cmsMeetings = await client.getCMSMeetings();
    console.log('ועידות CMS:', cmsMeetings);
    
  } catch (error) {
    console.error('שגיאה בניהול ועידות:', error.message);
  }
}

// דוגמה 8: סינכרון
async function syncOperations() {
  try {
    // בדיקת סטטוס סינכרון
    const status = await client.getSyncStatus();
    console.log('סטטוס סינכרון:', status);
    
    // הפעלת סינכרון מלא
    const syncResult = await client.triggerFullSync();
    console.log('תוצאת סינכרון:', syncResult);
    
    // הפעלת סינכרון למערכת ספציפית
    const cucmSync = await client.triggerSync('cucm');
    console.log('סינכרון CUCM:', cucmSync);
    
  } catch (error) {
    console.error('שגיאה בפעולות סינכרון:', error.message);
  }
}

// דוגמה 9: סקירת מערכת
async function getSystemOverview() {
  try {
    const overview = await client.getSystemOverview();
    console.log('סקירת מערכת:');
    console.log('מכשירים:', overview.devices);
    console.log('משתמשים:', overview.users);
    console.log('וועידות:', overview.meetings);
    console.log('בריאות:', overview.health);
    
    return overview;
  } catch (error) {
    console.error('שגיאה בקבלת סקירת מערכת:', error.message);
  }
}

// דוגמה 10: פונקציה מתקדמת מורכבת
async function complexWorkflow() {
  try {
    console.log('=== תחילת תהליך מורכב ===');
    
    // 1. בדיקת בריאות ה-API
    const health = await client.healthCheck();
    console.log('סטטוס API:', health.status);
    
    // 2. קבלת סקירת מערכת
    const overview = await client.getSystemOverview();
    console.log(`מצאתי ${overview.devices.total} מכשירים`);
    
    // 3. יצירת מכשיר חדש
    const newDevice = await client.createDevice({
      name: `SEP${Date.now()}`,
      ip_address: '192.168.1.200',
      mac_address: 'AA:BB:CC:DD:EE:FF',
      device_type: 'Cisco 8861',
      status: 'online',
      source: 'census'
    });
    console.log('מכשיר חדש נוצר:', newDevice.name);
    
    // 4. יצירת משתמש חדש
    const newUser = await client.createUser({
      user_id: `user${Date.now()}`,
      name: 'Test User',
      email: 'test@example.com',
      source: 'cucm'
    });
    console.log('משתמש חדש נוצר:', newUser.name);
    
    // 5. יצירת ועידה חדשה
    const newMeeting = await client.createMeetingRoom({
      meeting_id: `CONF${Date.now()}`,
      name: 'Test Meeting',
      passcode: '123456'
    });
    console.log('ועידה חדשה נוצרה:', newMeeting.name);
    
    // 6. הפעלת סינכרון
    await client.triggerFullSync();
    console.log('סינכרון הופעל');
    
    // 7. בדיקת תוצאות
    const finalOverview = await client.getSystemOverview();
    console.log('סקירה סופיתת:');
    console.log(`מכשירים: ${finalOverview.devices.total}`);
    console.log(`משתמשים: ${finalOverview.users.total}`);
    console.log(`וועידות: ${finalOverview.meetings.total}`);
    
    console.log('=== תהליך הסתיים בהצלחה ===');
    
  } catch (error) {
    console.error('שגיאה בתהליך המורכב:', error.message);
  }
}

// הפעלת הדוגמאות
async function runExamples() {
  console.log('הפעלת דוגמאות Census Client SDK...\n');
  
  // הרצת כל הדוגמאות
  await getAllDevices();
  await addNewDevice();
  await updateDevice();
  await getCUCMDevices();
  await registerPhone();
  await manageUsers();
  await manageMeetings();
  await syncOperations();
  await getSystemOverview();
  await complexWorkflow();
}

// אם הקובץ רץ ישירות, הפעל את הדוגמאות
if (require.main === module) {
  runExamples().catch(console.error);
}

// ייצוא הפונקציות לשימוש בקבצים אחרים
module.exports = {
  CensusClient,
  getAllDevices,
  addNewDevice,
  updateDevice,
  getCUCMDevices,
  registerPhone,
  manageUsers,
  manageMeetings,
  syncOperations,
  getSystemOverview,
  complexWorkflow
};
