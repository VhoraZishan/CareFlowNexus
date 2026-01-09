from fastapi import APIRouter
from app.models.schemas import CreatePatientRequest
from app.services.role_guard import require_role
from app.core.firebase import db
from datetime import datetime
import uuid

router = APIRouter(prefix="/patients")

@router.post("")
def create_patient(data: CreatePatientRequest):
    require_role(data.user_id, ["receptionist"])

    pid = str(uuid.uuid4())

    patient = {
        "patient_id": pid,
        "name": data.name,
        "age": data.age,
        "gender": data.gender,
        "medical_history": data.medical_history,
        "special_needs": data.special_needs,
        "status": "created",
        "created_by": data.user_id,
        "created_at": datetime.utcnow(),
        "admission": {}
    }

    db.collection("patients").document(pid).set(patient)
    return {"patient_id": pid, "status": "created"}

@router.get("")
def list_patients(user_id: str):
    user = require_role(user_id, ["receptionist", "doctor", "nurse"])

    patients = []
    for doc in db.collection("patients").stream():
        p = doc.to_dict()

        if user["role"] == "receptionist":
            patients.append(p)

        elif user["role"] == "doctor" and p["status"] in ["created", "admitted"]:
            patients.append(p)

        elif user["role"] == "nurse" and p.get("admission", {}).get("nurse_id") == user_id:
            patients.append(p)

    return patients
