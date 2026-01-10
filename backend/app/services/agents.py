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
    """Call bed assignment agent with error handling and fallback"""
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
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        logger.error(f"Bed agent API error {e.response.status_code}: {error_detail}")
        # Fallback: return first available bed if any
        if available_beds:
            first_bed = available_beds[0]
            return {
                "recommended_bed_id": first_bed.get("bed_id"),
                "reason": f"Fallback assignment due to agent API error ({e.response.status_code})",
                "recommendations": [{
                    "bed_id": first_bed.get("bed_id"),
                    "bed_number": first_bed.get("bed_number"),
                    "ward": first_bed.get("ward"),
                    "score": 50,  # Default score
                    "reasoning": f"Fallback due to agent error ({e.response.status_code})",
                    "pros": [],
                    "cons": []
                }],
                "confidence": 50
            }
        return {
            "recommended_bed_id": None,
            "reason": f"No beds available and agent API error ({e.response.status_code})",
            "recommendations": [],
            "confidence": 0
        }
    except httpx.TimeoutException:
        logger.error(f"Timeout calling bed agent at {BED_AGENT_URL}")
        # Fallback: return first available bed if any
        if available_beds:
            first_bed = available_beds[0]
            return {
                "recommended_bed_id": first_bed.get("bed_id"),
                "reason": "Fallback assignment due to agent timeout",
                "recommendations": [{
                    "bed_id": first_bed.get("bed_id"),
                    "bed_number": first_bed.get("bed_number"),
                    "ward": first_bed.get("ward"),
                    "score": 50,  # Default score
                    "reasoning": "Fallback due to agent timeout",
                    "pros": [],
                    "cons": []
                }],
                "confidence": 50
            }
        return {
            "recommended_bed_id": None,
            "reason": "No beds available and agent timeout",
            "recommendations": [],
            "confidence": 0
        }
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling bed agent: {e}")
        # Fallback: return first available bed if any
        if available_beds:
            first_bed = available_beds[0]
            return {
                "recommended_bed_id": first_bed.get("bed_id"),
                "reason": "Fallback assignment due to agent connection error",
                "recommendations": [{
                    "bed_id": first_bed.get("bed_id"),
                    "bed_number": first_bed.get("bed_number"),
                    "ward": first_bed.get("ward"),
                    "score": 50,  # Default score
                    "reasoning": "Fallback due to agent connection error",
                    "pros": [],
                    "cons": []
                }],
                "confidence": 50
            }
        return {
            "recommended_bed_id": None,
            "reason": "No beds available and agent connection error",
            "recommendations": [],
            "confidence": 0
        }
    except Exception as e:
        logger.error(f"Error calling bed agent: {e}")
        # Fallback: return first available bed if any
        if available_beds:
            first_bed = available_beds[0]
            return {
                "recommended_bed_id": first_bed.get("bed_id"),
                "reason": f"Fallback assignment due to error: {str(e)}",
                "recommendations": [{
                    "bed_id": first_bed.get("bed_id"),
                    "bed_number": first_bed.get("bed_number"),
                    "ward": first_bed.get("ward"),
                    "score": 50,  # Default score
                    "reasoning": f"Fallback due to error: {str(e)}",
                    "pros": [],
                    "cons": []
                }],
                "confidence": 50
            }
        return {
            "recommended_bed_id": None,
            "reason": f"No beds available and agent error: {str(e)}",
            "recommendations": [],
            "confidence": 0
        }


def call_nurse_agent(patient, bed, available_nurses):
    """Call nurse assignment agent with error handling and fallback"""
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
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        logger.error(f"Nurse agent API error {e.response.status_code}: {error_detail}")
        # Fallback: return first available nurse
        if available_nurses:
            return {
                "selected_nurse_id": available_nurses[0].get("user_id"),
                "reason": f"Fallback assignment due to agent API error ({e.response.status_code})"
            }
        return {
            "selected_nurse_id": None,
            "reason": f"No nurses available and agent API error ({e.response.status_code})"
        }
    except httpx.TimeoutException:
        logger.error(f"Timeout calling nurse agent at {NURSE_AGENT_URL}")
        # Fallback: return first available nurse
        if available_nurses:
            return {
                "selected_nurse_id": available_nurses[0].get("user_id"),
                "reason": "Fallback assignment due to agent timeout"
            }
        return {
            "selected_nurse_id": None,
            "reason": "No nurses available and agent timeout"
        }
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling nurse agent: {e}")
        # Fallback: return first available nurse
        if available_nurses:
            return {
                "selected_nurse_id": available_nurses[0].get("user_id"),
                "reason": "Fallback assignment due to agent connection error"
            }
        return {
            "selected_nurse_id": None,
            "reason": "No nurses available and agent connection error"
        }
    except Exception as e:
        logger.error(f"Error calling nurse agent: {e}")
        # Fallback: return first available nurse
        if available_nurses:
            return {
                "selected_nurse_id": available_nurses[0].get("user_id"),
                "reason": f"Fallback assignment due to error: {str(e)}"
            }
        return {
            "selected_nurse_id": None,
            "reason": f"No nurses available and agent error: {str(e)}"
        }


def call_cleaner_agent(bed, available_cleaners, context="post_discharge"):
    """Call cleaner assignment agent with error handling and fallback"""
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
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        logger.error(f"Cleaner agent API error {e.response.status_code}: {error_detail}")
        # Fallback: return first available cleaner
        if available_cleaners:
            return {
                "selected_cleaner_id": available_cleaners[0].get("user_id"),
                "reason": f"Fallback assignment due to agent API error ({e.response.status_code})"
            }
        return {
            "selected_cleaner_id": None,
            "reason": f"No cleaners available and agent API error ({e.response.status_code})"
        }
    except httpx.TimeoutException:
        logger.error(f"Timeout calling cleaner agent at {CLEANER_AGENT_URL}")
        # Fallback: return first available cleaner
        if available_cleaners:
            return {
                "selected_cleaner_id": available_cleaners[0].get("user_id"),
                "reason": "Fallback assignment due to agent timeout"
            }
        return {
            "selected_cleaner_id": None,
            "reason": "No cleaners available and agent timeout"
        }
    except httpx.ConnectError as e:
        logger.error(f"Connection error calling cleaner agent: {e}")
        # Fallback: return first available cleaner
        if available_cleaners:
            return {
                "selected_cleaner_id": available_cleaners[0].get("user_id"),
                "reason": "Fallback assignment due to agent connection error"
            }
        return {
            "selected_cleaner_id": None,
            "reason": "No cleaners available and agent connection error"
        }
    except Exception as e:
        logger.error(f"Error calling cleaner agent: {e}")
        # Fallback: return first available cleaner
        if available_cleaners:
            return {
                "selected_cleaner_id": available_cleaners[0].get("user_id"),
                "reason": f"Fallback assignment due to error: {str(e)}"
            }
        return {
            "selected_cleaner_id": None,
            "reason": f"No cleaners available and agent error: {str(e)}"
        }
