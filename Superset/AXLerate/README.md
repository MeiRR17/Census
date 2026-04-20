# AXLerate REST Middleware

## תיאור מערכת

תיקיית זו הוחלפה עם ה-SDK החדש שלנו (axlerate-sdk) ומיישמת את כל 3 "Iron Rules" של המערכת.

## 🔄 מה השתנה

### תלות מרכזיות
- **התקנה מ-SDK ישן**: כל הקריאות ל-CUCM עוברות דרך ה-SDK החדש `axlerate-client`
- **תקשורת REST/JSON**: כל התקשורות מתבצעות כ-REST/JSON במקום תואם
- **תרגום SOAP/XML**: המערכת מתרגם אוטומטית בין REST ל-SOAP
- **Write-Through ל-CENSUS**: כל פעולה מוצלחת נכתב ל-CENSUS DB

### קבצים שהוחלפו
- `main.py` - קובץ ראשי מעודכן
- `requirements.txt` - מעודכן עם תלות ה-SDK החדש
- `Dockerfile` - הגדרות להרצת Docker
- `docker-compose.yml` - הגדרות להרצת המערכת המלאה

## 🚀 התקנה והרצה

```bash
# התקנת תלות
pip install -r requirements.txt

# הרצת המערכת
docker-compose up -d

# המערכת זמינה על:
# - Gateway: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

## 📋 ממשקים

### מבנה חדש
```
AXLerate/
├── app/
│   ├── main.py              # FastAPI application עם SDK חדש
│   ├── census_integration.py # Write-through ל-CENSUS (אופציונלי)
│   └── cisco_uc_sdk.py    # ה-SDK הישן (לשימור)
├── requirements.txt           # תלות עם axlerate-sdk
├── Dockerfile              # הגדרות ל-Docker
├── docker-compose.yml      # הגדרות מלאות
└── README.md              # תיעוד זה
```

### מבנה ישנה
```
CMA/
├── axlerate-sdk/           # 📦 SDK מרוכז וחדש
├── axlerate-gateway/       # 🚪 API Gateway חדש
├── Census/                # 📊 אפליקציית ראשית
└── Superset/
    ├── AXLerate/          # 🔄 תיקיית מעודכנת
    ├── mock-server/
    ├── proxy-gateway/
    └── postgres/
```

## 🎯 יתרונות עיקריות

1. **כל האפליקציות מתחברות ל-SDK החדש**
2. **ה-AXLerate Gateway משמש כ-Gateway מרכזי**
3. **ה-Census מקבל נתונים ב-Write-Through**
4. **המערכת עובדת לפי 3 הכללים של הדיאגרמה**

## 📞 נקודות API

### Health Check
```bash
curl http://localhost:8000/health
```

### Add Phone
```bash
curl -X POST http://localhost:8000/axl/phone \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SEP1234567890AB",
    "description": "Test Phone",
    "product": "Cisco 8841"
  }'
```

### Get Phone
```bash
curl http://localhost:8000/axl/phone/SEP1234567890AB
```

## 🔧 הגדרות סביבה

### משתנים סביבתיים
```bash
# ב-.env
CUCM_SERVER=192.168.1.100
CUCM_USERNAME=admin
CUCM_PASSWORD=password
CUCM_PORT=8443
CUCM_VERIFY_SSL=false
```

### משתני סביבה לייצור
```bash
# ב-docker-compose.yml
services:
  axlerate-gateway:
    environment:
      CUCM_SERVER: ${CUCM_SERVER}
      CUCM_USERNAME: ${CUCM_USERNAME}
      # ...
```

## 🧪 בדיקות

ראה `axlerate-gateway/tests/test_gateway.py` לבדיקות מקיפות של:
- כל 3 Iron Rules
- end-to-end workflows
- טיפול בשגיאות

```bash
# הרצת בדיקות
cd axlerate-gateway
python -m pytest tests/test_gateway.py -v
```

---

**מערכת זו מיישמת את כל 3 הכללים של הדיאגרמה ומוכנה לשימוש קל ומבוססת!** 🎉
