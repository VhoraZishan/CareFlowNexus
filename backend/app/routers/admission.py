from app.core.firebase import db
from app.models.schemas import AdmissionRequest, ConfirmBedRequest
from app.services.agents import call_bed_agent, call_cleaner_agent, call_nurse_agent
from app.services.role_guard import require_role
from app.services.tasks import create_task
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
    try:
        agent_result = call_bed_agent(patient_payload, doctor_payload, beds)
        print("BED AGENT RESULT =", agent_result)
    except Exception as e:
        print(f"Bed Agent failed: {e}")
        agent_result = {"reason": "AI Agent Offline - Request forwarded to Admin", "recommended_bed_id": None}

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
    patient = patient_ref.get().to_dict()
    bed_ref = db.collection("beds").document(data.bed_id)
    bed = bed_ref.get().to_dict()

    # Update patient status to "bed_confirmed"
    patient_ref.update(
        {
            "status": "bed_confirmed",
            "admission.confirmed_bed_id": data.bed_id,
            "admission.confirmed_by": data.user_id,
        }
    )

    # Lock bed
    bed_ref.update({"occupied": True, "current_patient_id": patient_id})

    # ✅ SPECIFICATION: Call CLEANER AGENT for pre-admission bed preparation
    # Section 3.3: "Called when bed is confirmed for admission"
    cleaners = [
        c.to_dict()
        for c in db.collection("users")
        .where("role", "==", "cleaner")
        .where("active", "==", True)
        .stream()
    ]

    # Call cleaner agent with "pre_admission" context
    cleaner_result = call_cleaner_agent(bed, cleaners, context="pre_admission")
    print("CLEANER AGENT RESULT (pre_admission) =", cleaner_result)

    cleaner_id = cleaner_result.get("selected_cleaner_id")

    if cleaner_id:
        # Create cleaner task for bed preparation
        create_task(
            task_type="cleaning",
            role="cleaner",
            patient_id=patient_id,
            bed_id=data.bed_id,
            assigned_to=cleaner_id,
        )

        return {
            "status": "bed_confirmed",
            "message": "Bed confirmed. Cleaner assigned for preparation.",
            "assigned_cleaner_id": cleaner_id,
            "next_step": "Cleaner must prepare bed, then nurse will be assigned",
        }
    else:
        return {
            "status": "bed_confirmed",
            "message": "Bed confirmed but no cleaner available",
            "warning": "Manual bed preparation required",
        }
