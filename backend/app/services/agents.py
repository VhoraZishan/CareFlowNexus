import os

<<<<<<< HEAD
import httpx

BED_AGENT_URL = os.getenv("BED_AGENT_URL", "http://localhost:9000/agent/bed-assignment")
CLEANER_AGENT_URL = os.getenv(
    "CLEANER_AGENT_URL", "http://localhost:9000/agent/cleaner-assignment"
)
NURSE_AGENT_URL = os.getenv(
    "NURSE_AGENT_URL", "http://localhost:9000/agent/nurse-assignment"
)

=======
BED_AGENT_URL = os.getenv("BED_AGENT_URL", "http://localhost:9000/agent/bed-assignment")
CLEANER_AGENT_URL = os.getenv("CLEANER_AGENT_URL", "http://localhost:9000/agent/cleaner-assignment")
NURSE_AGENT_URL = os.getenv("NURSE_AGENT_URL", "http://localhost:9000/agent/nurse-assignment")
>>>>>>> dacac6ce13b9167cac683145f68d78d876c7cdec

def call_bed_agent(patient, doctor_input, available_beds):
    payload = {
        "patient": patient,
        "doctor_input": doctor_input,
        "available_beds": available_beds,
    }
    return httpx.post(BED_AGENT_URL, json=payload, timeout=10).json()


def call_nurse_agent(patient, bed, available_nurses):
    payload = {"patient": patient, "bed": bed, "available_nurses": available_nurses}
    return httpx.post(NURSE_AGENT_URL, json=payload).json()


def call_cleaner_agent(bed, available_cleaners):
    payload = {
        "bed_id": bed.get("bed_id") if isinstance(bed, dict) else bed,
        "available_cleaners": available_cleaners,
        "context": "post_discharge",
    }
    return httpx.post(CLEANER_AGENT_URL, json=payload).json()
