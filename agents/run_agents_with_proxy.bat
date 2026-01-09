@echo off
echo ================================================
echo CareFlow Agents - Starting with Proxy
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [2/3] Starting Pure Agent Server on port 9001...
start "Pure Agent Server" cmd /k "call venv\Scripts\activate.bat && python agent_server_pure.py"

REM Wait for agent server to start
timeout /t 3 /nobreak > nul

echo [3/3] Starting Proxy Server on port 9000...
echo.
echo ================================================
echo ARCHITECTURE:
echo   Backend (port 8000)
echo      ↓
echo   Proxy (port 9000) - Cleans Firestore data
echo      ↓
echo   Pure Agents (port 9001) - Pure computation
echo ================================================
echo.
echo Proxy will forward cleaned requests to agents
echo Backend should connect to: http://localhost:9000
echo.
echo Press Ctrl+C to stop the proxy
echo (Pure agent server runs in separate window)
echo.

REM Run the proxy (this window)
python agent_proxy.py

REM Deactivate on exit
deactivate
