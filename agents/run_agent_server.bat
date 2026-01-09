@echo off
echo ================================================
echo CareFlow AI Agent Server - Windows Startup
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

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo Please create .env file with:
    echo   FIREBASE_SERVICE_ACCOUNT_PATH=./config/serviceAccountKey.json
    echo   GOOGLE_API_KEY=your_gemini_api_key
    echo   GEMINI_MODEL=gemini-2.0-flash-exp
    echo.
    pause
    exit /b 1
)

REM Check if service account exists
if not exist "config\serviceAccountKey.json" (
    echo.
    echo [WARNING] Firebase service account not found!
    echo Please place your serviceAccountKey.json in config/ folder
    echo.
    pause
    exit /b 1
)

echo [2/3] Configuration validated
echo [3/3] Starting Agent Server...
echo.
echo Server will be available at: http://localhost:9000
echo API Documentation: http://localhost:9000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the agent server
python agent_server.py

REM Deactivate on exit
deactivate
