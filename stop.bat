@echo off
echo Stopping Quant System...
docker compose down >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>nul
echo Stopped Docker and local processes on ports 3000/8000.
pause
