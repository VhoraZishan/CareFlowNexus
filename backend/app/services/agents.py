import os

import httpx
from app.utils.serializers import serialize_firestore_data

BED_AGENT_URL = os.getenv("BED_AGENT_URL", "http://localhost:9000/agent/bed-assignment")
CLEANER_AGENT_URL = os.getenv(
    "CLEANER_AGENT_URL", "http://localhost:9000/agent/cleaner-assignment"
)
NURSE_AGENT_URL = os.getenv(
    "NURSE_AGENT_URL", "http://localhost:9000/agent/nurse-assignment"
)


def call_bed_agent(patient, doctor_input, available_beds):
    payload = {
        "patient": serialize_firestore_data(patient),
        "doctor_input": serialize_firestore_data(doctor_input),
        "available_beds": serialize_firestore_data(available_beds),
    }
    return httpx.post(BED_AGENT_URL, json=payload, timeout=10).json()


def call_nurse_agent(patient, bed, available_nurses):
    payload = {
        "patient": serialize_firestore_data(patient),
        "bed": serialize_firestore_data(bed),
        "available_nurses": serialize_firestore_data(available_nurses),
    }
    return httpx.post(NURSE_AGENT_URL, json=payload).json()


def call_cleaner_agent(bed, available_cleaners, context="post_discharge"):
    payload = {
        "bed_id": bed.get("bed_id") if isinstance(bed, dict) else bed,
        "available_cleaners": serialize_firestore_data(available_cleaners),
        "context": context,  # "pre_admission" or "post_discharge"
    }
    return httpx.post(CLEANER_AGENT_URL, json=payload).json()
