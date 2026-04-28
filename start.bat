@echo off
setlocal
echo Starting Quant System...
echo.

echo [1/2] Trying Docker mode first...
docker info >nul 2>nul
if errorlevel 1 goto :LOCAL_FALLBACK

docker compose down >nul 2>nul
docker compose up -d --build
if errorlevel 1 goto :LOCAL_FALLBACK

echo.
echo ============================================
echo   Ready! Docker services are running.
echo   Frontend: http://localhost
echo   Backend API Docs: http://localhost:8000/docs
echo ============================================
timeout /t 3 >nul
start http://localhost
endlocal
exit /b 0

:LOCAL_FALLBACK
echo.
echo [2/2] Docker unavailable. Falling back to Local mode...
echo.

if not exist "backend\venv\Scripts\python.exe" (
  echo [ERROR] Missing Python virtual environment: backend\venv
  echo Run:
  echo   cd backend
  echo   python -m venv venv
  echo   venv\Scripts\activate
  echo   pip install -r requirements-dev.txt
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [ERROR] Missing frontend dependencies: frontend\node_modules
  echo Run:
  echo   cd frontend
  echo   npm install
  pause
  exit /b 1
)

echo Starting backend on http://localhost:8000 ...
start "Quant Backend" cmd /c "cd /d "%CD%\backend" && venv\Scripts\python.exe run.py"

echo Starting frontend on http://localhost:3000 ...
start "Quant Frontend" cmd /c "cd /d "%CD%\frontend" && npm run dev -- --host 0.0.0.0 --port 3000"

echo.
echo ============================================
echo   Ready! Local services are starting.
echo   Frontend: http://localhost:3000
echo   Backend API Docs: http://localhost:8000/docs
echo ============================================
timeout /t 3 >nul
start http://localhost:3000
endlocal
exit /b 0
