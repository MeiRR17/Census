@echo off
color 0A
echo ===================================================
echo   Initiating Deployment to Standalone Server
echo ===================================================
echo.

:: הגדרת הנתיב המדויק לתוכנת השורת-פקודה של WinSCP
:: שים לב שאנו משתמשים ב-WinSCP.com ולא ב-WinSCP.exe
set WINSCP_PATH="C:\Program Files (x86)\WinSCP\WinSCP.com"

:: בדיקה שהתוכנה אכן מותקנת בנתיב המבוקש
if not exist %WINSCP_PATH% (
    echo [ERROR] WinSCP is not found at %WINSCP_PATH%.
    echo Please install it or correct the path in this script.
    pause
    exit /b 1
)

:: הרצת WinSCP עם קובץ הפקודות שיצרנו
echo [INFO] Connecting to Standalone Server...
echo [INFO] Uploading files and starting containers. This may take a moment...
echo.

%WINSCP_PATH% /script=winscp_axlerate_commands.txt

echo.
echo ===================================================
echo   [SUCCESS] Deployment Completed!
echo   The AXLerate Gateway is now running on the Standalone Server.
echo ===================================================
pause