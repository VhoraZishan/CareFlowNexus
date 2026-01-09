import logging
import os

import httpx
from app.utils.serializers import serialize_firestore_data

# Configure logging
logger = logging.getLogger(__name__)

BED_AGENT_URL = os.getenv("BED_AGENT_URL", "http://localhost:9000/agent/bed-assignment")
CLEANER_AGENT_URL = os.getenv(
    "CLEANER_AGENT_URL", "http://localhost:9000/agent/cleaner-assignment"
)
NURSE_AGENT_URL = os.getenv(
    "NURSE_AGENT_URL", "http://localhost:9000/agent/nurse-assignment"
)

# Log the configured URLs on startup
logger.info(f"BED_AGENT_URL: {BED_AGENT_URL}")
logger.info(f"CLEANER_AGENT_URL: {CLEANER_AGENT_URL}")
logger.info(f"NURSE_AGENT_URL: {NURSE_AGENT_URL}")


def call_bed_agent(patient, doctor_input, available_beds):
    """Call bed assignment agent with error handling"""
    payload = {
        "patient": serialize_firestore_data(patient),
        "doctor_input": serialize_firestore_data(doctor_input),
        "available_beds": serialize_firestore_data(available_beds),
    }

    try:
        logger.info(f"Calling bed agent at {BED_AGENT_URL}")
        response = httpx.post(BED_AGENT_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Bed agent response: {result}")
        return result
    except httpx.TimeoutException:
        logger.error(f"Timeout calling bed agent at {BED_AGENT_URL}")
        raise Exception(
            f"Bed agent timeout. Please check if agent service is running at {BED_AGENT_URL}"
        )
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling bed agent: {e}")
        raise Exception(
            f"Cannot connect to bed agent at {BED_AGENT_URL}. Service may be down."
        )
    except Exception as e:
        logger.error(f"Error calling bed agent: {e}")
        raise Exception(f"Bed agent error: {str(e)}")


def call_nurse_agent(patient, bed, available_nurses):
    """Call nurse assignment agent with error handling"""
    payload = {
        "patient": serialize_firestore_data(patient),
        "bed": serialize_firestore_data(bed),
        "available_nurses": serialize_firestore_data(available_nurses),
    }

    try:
        logger.info(f"Calling nurse agent at {NURSE_AGENT_URL}")
        response = httpx.post(NURSE_AGENT_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Nurse agent response: {result}")
        return result
    except httpx.TimeoutException:
        logger.error(f"Timeout calling nurse agent at {NURSE_AGENT_URL}")
        raise Exception(
            f"Nurse agent timeout. Please check if agent service is running at {NURSE_AGENT_URL}"
        )
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling nurse agent: {e}")
        raise Exception(
            f"Cannot connect to nurse agent at {NURSE_AGENT_URL}. Service may be down."
        )
    except Exception as e:
        logger.error(f"Error calling nurse agent: {e}")
        raise Exception(f"Nurse agent error: {str(e)}")


def call_cleaner_agent(bed, available_cleaners, context="post_discharge"):
    """Call cleaner assignment agent with error handling"""
    payload = {
        "bed_id": bed.get("bed_id") if isinstance(bed, dict) else bed,
        "available_cleaners": serialize_firestore_data(available_cleaners),
        "context": context,  # "pre_admission" or "post_discharge"
    }

    try:
        logger.info(
            f"Calling cleaner agent at {CLEANER_AGENT_URL} (context: {context})"
        )
        response = httpx.post(CLEANER_AGENT_URL, json=payload, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Cleaner agent response: {result}")
        return result
    except httpx.TimeoutException:
        logger.error(f"Timeout calling cleaner agent at {CLEANER_AGENT_URL}")
        raise Exception(
            f"Cleaner agent timeout. Please check if agent service is running at {CLEANER_AGENT_URL}"
        )
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling cleaner agent: {e}")
        raise Exception(
            f"Cannot connect to cleaner agent at {CLEANER_AGENT_URL}. Service may be down."
        )
    except Exception as e:
        logger.error(f"Error calling cleaner agent: {e}")
        raise Exception(f"Cleaner agent error: {str(e)}")
