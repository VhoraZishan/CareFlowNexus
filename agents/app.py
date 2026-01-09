"""
CareFlow Nexus - Hugging Face Spaces Entry Point
Main application file for Hugging Face deployment
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app
from api import app

# Hugging Face Spaces will automatically run this with uvicorn
if __name__ == "__main__":
    import uvicorn

    # Hugging Face Spaces uses port 7860 by default
    port = int(os.environ.get("PORT", 7860))

    print("=" * 60)
    print("Starting CareFlow Nexus on Hugging Face Spaces")
    print(f"Port: {port}")
    print("=" * 60)

    uvicorn.run(
        "api:app", host="0.0.0.0", port=port, reload=False, workers=1, log_level="info"
    )
