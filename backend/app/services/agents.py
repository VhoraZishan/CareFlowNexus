import httpx
import os

BED_AGENT_URL = os.getenv("BED_AGENT_URL", "http://localhost:9000/agent/bed-assignment")
CLEANER_AGENT_URL = os.getenv("CLEANER_AGENT_URL", "http://localhost:9000/agent/cleaner-assignment")
NURSE_AGENT_URL = os.getenv("NURSE_AGENT_URL", "http://localhost:9000/agent/nurse-assignment")

def call_bed_agent(patient, doctor_input, available_beds):
    payload = {
        "patient": patient,
        "doctor_input": doctor_input,
        "available_beds": available_beds
    }
    return httpx.post(BED_AGENT_URL, json=payload, timeout=10).json()

def call_nurse_agent(patient, bed, available_nurses):
    payload = {
        "patient": patient,
        "bed": bed,
        "available_nurses": available_nurses,
        "task_type": "discharge"
    }
    return httpx.post(NURSE_AGENT_URL, json=payload).json()


def call_cleaner_agent(bed, available_cleaners):
    payload = {
        "bed": bed,
        "available_cleaners": available_cleaners,
        "task_type": "post_discharge_cleaning"
    }
    return httpx.post(CLEANER_AGENT_URL, json=payload).json()
