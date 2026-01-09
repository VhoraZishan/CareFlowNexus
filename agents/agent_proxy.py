"""
Agent Proxy Server - Firestore Data Sanitizer
==============================================

This proxy sits between the backend and the pure agent server.
It cleans Firestore timestamps and other non-serializable data before forwarding requests.

Usage:
    python agent_proxy.py

The proxy runs on port 9000 (what backend expects)
and forwards to pure agents on port 9001
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CareFlow Agent Proxy",
    description="Sanitizes Firestore data before forwarding to agents",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PROXY_PORT = int(os.getenv("PROXY_PORT", "9000"))
AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL", "http://localhost:9001")


# ==================== DATA SANITIZATION ====================


def sanitize_firestore_data(data: Any) -> Any:
    """
    Recursively clean Firestore-specific types that cause JSON serialization errors

    Handles:
    - DatetimeWithNanoseconds
    - Timestamp objects
    - Other Firestore-specific types

    Args:
        data: Data to clean (dict, list, or primitive)

    Returns:
        Cleaned data that can be JSON serialized
    """
    if data is None:
        return None

    # Handle dictionaries
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # Skip timestamp fields entirely (agents don't need them)
            if key in [
                "created_at",
                "updated_at",
                "completed_at",
                "timestamp",
                "requested_at",
                "confirmed_at",
                "bed_prepared_at",
                "nurse_care_started_at",
            ]:
                logger.debug(f"Skipping timestamp field: {key}")
                continue

            # Recursively clean nested data
            cleaned[key] = sanitize_firestore_data(value)

        return cleaned

    # Handle lists
    elif isinstance(data, list):
        return [sanitize_firestore_data(item) for item in data]

    # Handle datetime objects (convert to ISO string)
    elif isinstance(data, datetime):
        return data.isoformat()

    # Handle any object with a timestamp-like name in its class
    elif hasattr(data, "__class__") and "Datetime" in data.__class__.__name__:
        logger.debug(
            f"Converting Firestore timestamp: {data.__class__.__name__} -> ISO string"
        )
        # Try to convert to ISO string
        try:
            if hasattr(data, "isoformat"):
                return data.isoformat()
            elif hasattr(data, "timestamp"):
                return datetime.fromtimestamp(data.timestamp()).isoformat()
            else:
                return str(data)
        except Exception as e:
            logger.warning(f"Could not convert timestamp: {e}")
            return None

    # Return primitives as-is
    else:
        return data


# ==================== PROXY ENDPOINTS ====================


@app.get("/health")
async def health_check():
    """Health check - also checks if agent server is reachable"""
    try:
        response = httpx.get(f"{AGENT_SERVER_URL}/health", timeout=2)
        agent_healthy = response.status_code == 200
    except Exception as e:
        logger.warning(f"Agent server health check failed: {e}")
        agent_healthy = False

    return {
        "status": "healthy",
        "proxy_status": "running",
        "agent_server_status": "healthy" if agent_healthy else "unreachable",
        "agent_server_url": AGENT_SERVER_URL,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/agent/bed-assignment")
async def proxy_bed_assignment(request: Request):
    """
    Proxy for bed assignment agent
    Cleans Firestore data and forwards to real agent
    """
    try:
        # Get raw request body
        body = await request.json()

        logger.info("Received bed assignment request")
        logger.debug(f"Raw request keys: {body.keys()}")

        # Sanitize data
        clean_body = sanitize_firestore_data(body)

        logger.info(
            f"Forwarding to agent server: {AGENT_SERVER_URL}/agent/bed-assignment"
        )

        # Forward to real agent server
        response = httpx.post(
            f"{AGENT_SERVER_URL}/agent/bed-assignment",
            json=clean_body,
            timeout=30,
        )

        # Return agent response
        result = response.json()
        logger.info(f"Agent response: {result.get('recommended_bed_id')}")
        return result

    except httpx.RequestError as e:
        logger.error(f"Error connecting to agent server: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent server unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in bed assignment proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


@app.post("/agent/cleaner-assignment")
async def proxy_cleaner_assignment(request: Request):
    """
    Proxy for cleaner assignment agent
    Cleans Firestore data and forwards to real agent
    """
    try:
        # Get raw request body
        body = await request.json()

        logger.info(
            f"Received cleaner assignment request (context: {body.get('context')})"
        )

        # Sanitize data
        clean_body = sanitize_firestore_data(body)

        logger.info(
            f"Forwarding to agent server: {AGENT_SERVER_URL}/agent/cleaner-assignment"
        )

        # Forward to real agent server
        response = httpx.post(
            f"{AGENT_SERVER_URL}/agent/cleaner-assignment",
            json=clean_body,
            timeout=30,
        )

        # Return agent response
        result = response.json()
        logger.info(f"Agent response: {result.get('selected_cleaner_id')}")
        return result

    except httpx.RequestError as e:
        logger.error(f"Error connecting to agent server: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent server unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in cleaner assignment proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


@app.post("/agent/nurse-assignment")
async def proxy_nurse_assignment(request: Request):
    """
    Proxy for nurse assignment agent
    Cleans Firestore data and forwards to real agent
    """
    try:
        # Get raw request body
        body = await request.json()

        logger.info("Received nurse assignment request")
        logger.debug(f"Patient ID: {body.get('patient', {}).get('patient_id')}")

        # Sanitize data
        clean_body = sanitize_firestore_data(body)

        logger.info(
            f"Forwarding to agent server: {AGENT_SERVER_URL}/agent/nurse-assignment"
        )

        # Forward to real agent server
        response = httpx.post(
            f"{AGENT_SERVER_URL}/agent/nurse-assignment",
            json=clean_body,
            timeout=30,
        )

        # Return agent response
        result = response.json()
        logger.info(f"Agent response: {result.get('selected_nurse_id')}")
        return result

    except httpx.RequestError as e:
        logger.error(f"Error connecting to agent server: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent server unavailable: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in nurse assignment proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


# ==================== MAIN ====================


if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info("CareFlow Agent Proxy Server Starting...")
    logger.info("=" * 60)
    logger.info(f"Proxy Port: {PROXY_PORT}")
    logger.info(f"Agent Server URL: {AGENT_SERVER_URL}")
    logger.info("")
    logger.info("This proxy:")
    logger.info("  1. Receives requests from backend (with Firestore timestamps)")
    logger.info("  2. Cleans/sanitizes the data")
    logger.info("  3. Forwards clean data to pure agent server")
    logger.info("")
    logger.info("Architecture:")
    logger.info(
        f"  Backend → Proxy (:{PROXY_PORT}) → Pure Agents (:{AGENT_SERVER_URL.split(':')[-1]})"
    )
    logger.info("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT)
