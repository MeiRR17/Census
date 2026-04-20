# test_sdk.py
from axlerate.client import BaseCiscoClient  # שימוש במחלקת הבסיס של ה-SDK

def test_my_sdk():
    print("Starting SDK Test...")
    
    # 1. יצירת החיבור (הכנס את הכתובת של שרת ה-AXLerate המקומי או המוק שלך)
    # שים לב לשים את הפורט הנכון שAXLerate רץ עליו במחשב שלך
    client = BaseCiscoClient(
        server_ip="localhost",
        username="admin",
        password="admin",
        port=8000  # פורט ברירת המחדל של AXLerate
    )
    
    try:
        # 2. נסה להפעיל פונקציה פשוטה שקיימת ב-SDK שלך
        # (החלף את check_health בפונקציה אמיתית שכתבת, למשל ניסיון משיכת נתונים)
        print("Testing Connection...")
        
        # בדיקת חיבור בסיסית
        if hasattr(client, 'test_connection'):
            response = client.test_connection()
        else:
            # אם אין פונקציית test_connection, נבדור אם האובייקט נוצר בהצלחה
            response = {"status": "SDK Client created successfully", "server": client.server}
        
        print(f"Success! Server responded: {response}")
        
    except Exception as e:
        print(f"Failed! Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_my_sdk()
