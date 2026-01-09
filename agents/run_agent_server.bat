@echo off
echo ================================================
echo CareFlow Pure Agent Server - Windows Startup
echo (No Database Access - Backend Only)
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
echo [1/2] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists (optional for pure server)
if not exist ".env" (
    echo.
    echo [INFO] .env file not found - using defaults
    echo Pure agent server does not require database credentials
    echo.
)

echo [2/2] Starting Pure Agent Server...
echo.
echo Server will be available at: http://localhost:9000
echo API Documentation: http://localhost:9000/docs
echo.
echo THIS SERVER DOES NOT ACCESS DATABASE
echo All data comes from backend requests
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the PURE agent server (no database dependencies)
python agent_server_pure.py

REM Deactivate on exit
deactivate
