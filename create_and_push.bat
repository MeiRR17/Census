@echo off
echo Creating CMA repository on GitHub...
echo.
echo Please make sure you are logged into GitHub in your browser.
echo.
echo Steps:
echo 1. Go to https://github.com/MeiRR17
echo 2. Click "New" button
echo 3. Repository name: CMA
echo 4. Description: Unified CMA project with Census and Superset modules
echo 5. Choose Public or Private
echo 6. UNCHECK "Add a README file"
echo 7. Click "Create repository"
echo.
pause
echo.
echo Pushing code to GitHub...
git push -u origin master
echo.
echo Done! Your repository is now available at: https://github.com/MeiRR17/CMA
pause
