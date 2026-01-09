from fastapi import APIRouter
from app.models.schemas import CreatePatientRequest, DischargeRequest
from app.services.role_guard import require_role
from app.core.firebase import db
from datetime import datetime
import uuid
from app.services.agents import call_nurse_agent
from app.services.tasks import create_task

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

@router.post("/{patient_id}/discharge")
def request_discharge(patient_id: str, data: DischargeRequest):
    # Role check
    require_role(data.user_id, ["doctor"])

    patient_ref = db.collection("patients").document(patient_id)
    patient_doc = patient_ref.get()

    if not patient_doc.exists:
        raise HTTPException(404, "Patient not found")

    patient = patient_doc.to_dict()

    if patient["status"] not in ["admitted", "under_care"]:
        raise HTTPException(400, "Patient not eligible for discharge")

    # Fetch bed
    bed_id = patient["admission"]["confirmed_bed_id"]
    bed = db.collection("beds").document(bed_id).get().to_dict()

    # Fetch nurses
    nurses = [
        n.to_dict()
        for n in db.collection("users")
        .where("role", "==", "nurse")
        .where("active", "==", True)
        .stream()
    ]

    # Call nurse assignment agent
    agent_result = call_nurse_agent(patient, bed, nurses)

    nurse_id = agent_result["selected_nurse_id"]

    # Update patient
    patient_ref.update({
        "status": "discharge_requested",
        "discharge": {
            "requested_by": data.user_id,
            "notes": data.discharge_notes,
            "requested_at": datetime.utcnow()
        }
    })

    # Create nurse discharge task
    create_task(
        task_type="discharge_nursing",
        role="nurse",
        patient_id=patient_id,
        bed_id=bed_id,
        assigned_to=nurse_id
    )

    return {
        "status": "discharge_requested",
        "assigned_nurse_id": nurse_id
    }
