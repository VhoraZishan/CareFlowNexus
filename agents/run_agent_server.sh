#!/bin/bash

echo "================================================"
echo "CareFlow AI Agent Server - Linux/Mac Startup"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "[1/3] Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] .env file not found!"
    echo "Please create .env file with:"
    echo "  FIREBASE_SERVICE_ACCOUNT_PATH=./config/serviceAccountKey.json"
    echo "  GOOGLE_API_KEY=your_gemini_api_key"
    echo "  GEMINI_MODEL=gemini-2.0-flash-exp"
    echo ""
    exit 1
fi

# Check if service account exists
if [ ! -f "config/serviceAccountKey.json" ]; then
    echo ""
    echo "[WARNING] Firebase service account not found!"
    echo "Please place your serviceAccountKey.json in config/ folder"
    echo ""
    exit 1
fi

echo "[2/3] Configuration validated"
echo "[3/3] Starting Agent Server..."
echo ""
echo "Server will be available at: http://localhost:9000"
echo "API Documentation: http://localhost:9000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the agent server
python agent_server.py

# Deactivate on exit
deactivate
