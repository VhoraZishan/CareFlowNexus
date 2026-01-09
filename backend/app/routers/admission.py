from fastapi import APIRouter
from app.models.schemas import AdmissionRequest, ConfirmBedRequest
from app.services.role_guard import require_role
from app.services.agents import call_bed_agent
from app.core.firebase import db

router = APIRouter(prefix="/patients")

@router.post("/{patient_id}/admission")
def admit_patient(patient_id: str, data: AdmissionRequest):
    require_role(data.user_id, ["doctor"])

    ref = db.collection("patients").document(patient_id)
    patient = ref.get().to_dict()

    beds = [b.to_dict() for b in db.collection("beds").where("occupied", "==", False).stream()]

    agent_result = call_bed_agent(patient, data.dict(), beds)

    ref.update({
        "status": "pending_confirmation",
        "admission": {
            "doctor_id": data.user_id,
            "diagnosis": data.diagnosis,
            "special_instructions": data.special_instructions,
            "recommended_bed_id": agent_result["recommended_bed_id"]
        }
    })

    return {
        "recommended_bed_id": agent_result["recommended_bed_id"],
        "status": "pending_confirmation"
    }

@router.post("/{patient_id}/confirm-bed")
def confirm_bed(patient_id: str, data: ConfirmBedRequest):
    require_role(data.user_id, ["receptionist"])

    patient_ref = db.collection("patients").document(patient_id)
    bed_ref = db.collection("beds").document(data.bed_id)

    patient_ref.update({
        "status": "admitted",
        "admission.confirmed_bed_id": data.bed_id
    })

    bed_ref.update({
        "occupied": True,
        "current_patient_id": patient_id
    })

    return {"status": "admitted"}
