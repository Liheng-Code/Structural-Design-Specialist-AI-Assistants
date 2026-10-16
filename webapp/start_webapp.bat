@echo off
rem Double-click. Starts the PT Designer mockup: API on port 8000, web app on http://localhost:3000
cd /d "%~dp0"
start "PT Designer API" cmd /k "cd /d api && py -m uvicorn main:app --host 127.0.0.1 --port 8000"
start "PT Designer web" cmd /k "cd /d web && npm run dev"
timeout /t 6 >nul
start http://localhost:3000
