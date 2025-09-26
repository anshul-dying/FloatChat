@echo off
echo Starting FloatChat Full Stack Application...
echo.
echo This will start both the backend API and frontend in separate windows.
echo.
echo Starting backend API server...
start "FloatChat API" cmd /k "cd /d %~dp0.. && call venv\Scripts\activate && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
echo.
echo Waiting 8 seconds for API to start...
timeout /t 8 /nobreak > nul
echo.
echo Starting frontend development server...
start "FloatChat Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev"
echo.
echo Both servers are starting up...
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window (servers will continue running)...
pause > nul
