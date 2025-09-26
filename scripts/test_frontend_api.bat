@echo off
echo Testing Frontend API Connection...
echo.
echo 1. Testing if frontend is running...
curl -s http://localhost:3000 > nul
if %errorlevel% equ 0 (
    echo ✓ Frontend is running on port 3000
) else (
    echo ✗ Frontend is NOT running on port 3000
    echo Please start the frontend first using: scripts\start_frontend.bat
    goto :end
)
echo.
echo 2. Testing if backend is running...
curl -s http://localhost:8000/health > nul
if %errorlevel% equ 0 (
    echo ✓ Backend is running on port 8000
) else (
    echo ✗ Backend is NOT running on port 8000
    echo Please start the backend first using: scripts\start_backend.bat
    goto :end
)
echo.
echo 3. Testing Vite proxy...
curl -X POST "http://localhost:3000/api/chat" -H "Content-Type: application/json" -d "{\"text\": \"test\", \"profession\": \"researcher\"}"
echo.
echo 4. Testing direct backend...
curl -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -d "{\"text\": \"test\", \"profession\": \"researcher\"}"
echo.
echo Test completed!
:end
pause
