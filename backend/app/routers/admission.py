from app.core.firebase import db
from app.models.schemas import AdmissionRequest, ConfirmBedRequest
from app.services.agents import call_bed_agent
from app.services.role_guard import require_role
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/patients")


@router.post("/{patient_id}/admission")
def admit_patient(patient_id: str, data: AdmissionRequest):
    require_role(data.user_id, ["doctor"])

    # Fetch patient
    ref = db.collection("patients").document(patient_id)
    patient = ref.get().to_dict()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch available beds
    beds = [
        b.to_dict()
        for b in db.collection("beds").where("occupied", "==", False).stream()
    ]

    # 🔒 Build STRICT agent payloads
    patient_payload = {
        "patient_id": patient_id,
        "age": patient.get("age"),
        "gender": patient.get("gender"),
        "medical_history": patient.get("medical_history", []),
        "special_needs": patient.get("special_needs", []),
    }

    doctor_payload = {
        "diagnosis": data.diagnosis,
        "special_instructions": data.special_instructions,
    }

    # Call bed agent
    agent_result = call_bed_agent(patient_payload, doctor_payload, beds)
    print("BED AGENT RESULT =", agent_result)

    bed_id = agent_result.get("recommended_bed_id")
    reason = agent_result.get("reason", "No reason provided")

    # Handle case where agent found no suitable bed
    if not bed_id:
        # Update patient with "no suitable bed" status
        ref.update(
            {
                "status": "admission_pending_bed",
                "admission": {
                    "doctor_id": data.user_id,
                    "diagnosis": data.diagnosis,
                    "special_instructions": data.special_instructions,
                    "recommended_bed_id": None,
                    "agent_message": reason,
                },
            }
        )

        return {
            "recommended_bed_id": None,
            "status": "admission_pending_bed",
            "message": reason,
            "suggestion": "Please add more beds with required features or adjust requirements",
        }

    # Update patient with recommended bed
    ref.update(
        {
            "status": "pending_confirmation",
            "admission": {
                "doctor_id": data.user_id,
                "diagnosis": data.diagnosis,
                "special_instructions": data.special_instructions,
                "recommended_bed_id": bed_id,
                "agent_message": reason,
            },
        }
    )

    return {
        "recommended_bed_id": bed_id,
        "status": "pending_confirmation",
        "reason": reason,
    }


@router.post("/{patient_id}/confirm-bed")
def confirm_bed(patient_id: str, data: ConfirmBedRequest):
    require_role(data.user_id, ["receptionist"])

    patient_ref = db.collection("patients").document(patient_id)
    bed_ref = db.collection("beds").document(data.bed_id)

    # Update patient
    patient_ref.update(
        {"status": "admitted", "admission.confirmed_bed_id": data.bed_id}
    )

    # Lock bed
    bed_ref.update({"occupied": True, "current_patient_id": patient_id})

    return {"status": "admitted"}
