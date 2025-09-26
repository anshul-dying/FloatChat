@echo off
echo Starting FloatChat Backend API...
cd /d "%~dp0.."
echo.
echo Activating virtual environment...
call venv\Scripts\activate
echo.
echo Starting FastAPI server with CORS enabled...
echo Backend will be available at: http://localhost:8000
echo API docs will be available at: http://localhost:8000/docs
echo.
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
pause
