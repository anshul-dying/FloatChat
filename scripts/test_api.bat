@echo off
echo Testing FloatChat API...
echo.
echo Testing health endpoint...
curl -X GET "http://localhost:8000/health"
echo.
echo.
echo Testing chat endpoint...
curl -X POST "http://localhost:8000/chat" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"Show me all ARGO floats\", \"profession\": \"researcher\"}"
echo.
echo.
echo API test completed!
pause
