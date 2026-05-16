@echo off
echo =========================================
echo Aether AI - GitHub Push Script
echo =========================================
echo.

cd /d "c:\users\daksh\Downloads\myy all project\project folder\google hack2skill"

echo [1/5] Removing .env from tracking to keep API key safe...
git rm --cached .env >nul 2>&1

echo [2/5] Adding all files...
git add .

echo [3/5] Committing changes...
git commit -m "Upload Aether-Ai with Groq migration" >nul 2>&1

echo [4/5] Fixing network connection issues...
git config --global http.postBuffer 524288000
git config --global http.sslVerify false
git config --global http.sslBackend schannel

echo [5/5] Pushing to GitHub...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/daksh473/Aether-Ai.git

git push -u origin main

if errorlevel 1 (
    echo.
    echo PUSH FAILED on 'main' branch. Trying 'master' branch instead...
    git push -u origin master
)

echo.
echo =========================================
echo Process Complete! Check if there are any errors above.
echo (If it still says "Connection was reset", try connecting to your Mobile Hotspot)
echo =========================================
pause
