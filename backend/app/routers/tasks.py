from datetime import datetime

from app.core.firebase import db
from app.models.schemas import TaskActionRequest, TaskCompleteRequest
from app.services.agents import call_cleaner_agent, call_nurse_agent
from app.services.role_guard import require_role
from app.services.tasks import create_task
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tasks")


@router.get("")
def get_tasks(user_id: str):
    require_role(user_id, ["cleaner", "nurse"])

    tasks = []
    for doc in db.collection("tasks").where("assigned_to", "==", user_id).stream():
        task = doc.to_dict()
        # Ensure task_id is included (Firestore doc.id might differ from task_id field)
        if task:
            task["task_id"] = task.get("task_id") or doc.id

            # Hydrate Patient details
            if task.get("patient_id"):
                p_doc = db.collection("patients").document(task["patient_id"]).get()
                if p_doc.exists:
                    task["patient_name"] = p_doc.to_dict().get("name", "Unknown")

            # Hydrate Bed details
            if task.get("bed_id"):
                b_doc = db.collection("beds").document(task["bed_id"]).get()
                if b_doc.exists:
                    b_data = b_doc.to_dict()
                    # Try to get room number, fallback to bed_id
                    task["room"] = b_data.get("room_number") or b_data.get("bed_id") or task["bed_id"]
            
            tasks.append(task)

    return tasks


@router.post("/{task_id}/accept")
def accept_task(task_id: str, data: TaskActionRequest):
    require_role(data.user_id, ["cleaner", "nurse"])

    task_ref = db.collection("tasks").document(task_id)
    task_doc = task_ref.get()

    if not task_doc.exists:
        raise HTTPException(404, "Task not found")

    task = task_doc.to_dict()

    # Role + ownership enforcement
    require_role(data.user_id, [task["role"]])

    if task["assigned_to"] != data.user_id:
        raise HTTPException(403, "Not your task")

    if task["status"] != "assigned":
        raise HTTPException(400, f"Task must be in 'assigned' status to accept. Current status: {task.get('status')}")

    # Update task status to accepted
    task_ref.update({"status": "accepted"})
    return {"status": "accepted", "message": "Task accepted successfully"}


@router.post("/{task_id}/complete")
def complete_task(task_id: str, data: TaskCompleteRequest):
    task_ref = db.collection("tasks").document(task_id)
    task_doc = task_ref.get()

    if not task_doc.exists:
        raise HTTPException(404, "Task not found")

    task = task_doc.to_dict()

    # Role + ownership enforcement
    require_role(data.user_id, [task["role"]])

    if task["assigned_to"] != data.user_id:
        raise HTTPException(403, "Not your task")

    if task["status"] != "accepted":
        raise HTTPException(400, "Task must be accepted first")

    # Mark task complete
    task_ref.update(
        {"status": "completed", "completed_at": datetime.utcnow(), "notes": data.notes}
    )

    # BRANCH LOGIC
    if task["type"] == "discharge_nursing":
        _handle_nurse_discharge_completion(task)

    elif task["type"] == "cleaning":
        # Determine context: pre-admission or post-discharge
        patient = db.collection("patients").document(task["patient_id"]).get().to_dict()

        # Check if this is pre-admission cleaning (patient status = bed_confirmed)
        # or post-discharge cleaning (patient status = discharged)
        if patient.get("status") == "bed_confirmed":
            result = _handle_pre_admission_cleaning_completion(task)
            return {
                "status": "completed",
                "workflow_branch": "pre_admission",
                "patient_status": patient.get("status"),
                **result
            }
        else:
            _handle_post_discharge_cleaning_completion(task)
            return {
                "status": "completed",
                "workflow_branch": "post_discharge",
                "patient_status": patient.get("status")
            }

    elif task["type"] == "patient_care":
        _handle_patient_care_completion(task)

    return {"status": "completed"}


def _handle_nurse_discharge_completion(task):
    patient_ref = db.collection("patients").document(task["patient_id"])
    patient = patient_ref.get().to_dict()

    # Update patient
    patient_ref.update(
        {"status": "discharged", "discharge.completed_at": datetime.utcnow()}
    )

    # Fetch cleaners
    cleaners = [
        c.to_dict()
        for c in db.collection("users")
        .where("role", "==", "cleaner")
        .where("active", "==", True)
        .stream()
    ]

    bed = db.collection("beds").document(task["bed_id"]).get().to_dict()

    # Call cleaner agent
    agent_result = call_cleaner_agent(bed, cleaners)

    cleaner_id = agent_result["selected_cleaner_id"]

    # Create cleaner task
    create_task(
        task_type="cleaning",
        role="cleaner",
        patient_id=task["patient_id"],
        bed_id=task["bed_id"],
        assigned_to=cleaner_id,
    )


def _handle_pre_admission_cleaning_completion(task):
    """
    Handle completion of pre-admission bed preparation
    Specification: Call NURSE AGENT after bed preparation is complete
    """
    patient_ref = db.collection("patients").document(task["patient_id"])
    patient = patient_ref.get().to_dict()
    bed = db.collection("beds").document(task["bed_id"]).get().to_dict()

    # Update patient status
    patient_ref.update(
        {"status": "bed_prepared", "admission.bed_prepared_at": datetime.utcnow()}
    )

    # ✅ SPECIFICATION: Call NURSE AGENT for patient care
    # Section 4.3: "Called when bed preparation is complete"
    nurses = [
        n.to_dict()
        for n in db.collection("users")
        .where("role", "==", "nurse")
        .where("active", "==", True)
        .stream()
    ]

    # Call nurse agent
    nurse_result = call_nurse_agent(patient, bed, nurses)
    print("NURSE AGENT RESULT (bed_prepared) =", nurse_result)

    nurses_found_count = len(nurses)

    nurse_id = nurse_result.get("selected_nurse_id")

    if nurse_id:
        # Create nurse care task
        create_task(
            task_type="patient_care",
            role="nurse",
            patient_id=task["patient_id"],
            bed_id=task["bed_id"],
            assigned_to=nurse_id,
        )

        # Update patient with nurse assignment
        patient_ref.update({"admission.assigned_nurse_id": nurse_id})

        return {
            "assigned_nurse_id": nurse_id,
            "message": "Bed prepared. Nurse assigned for patient care.",
            "nurses_found_count": nurses_found_count,
            "nurse_agent_result": nurse_result
        }
    else:
        return {
            "assigned_nurse_id": None,
            "message": "Bed prepared but no nurse available",
            "nurses_found_count": nurses_found_count,
            "nurse_agent_result": nurse_result
        }


def _handle_post_discharge_cleaning_completion(task):
    """
    Handle completion of post-discharge bed cleaning
    Free the bed for next patient
    """
    # Free bed
    db.collection("beds").document(task["bed_id"]).update(
        {"occupied": False, "current_patient_id": None}
    )


def _handle_patient_care_completion(task):
    """
    Handle completion of patient care task
    Patient is now fully admitted
    """
    patient_ref = db.collection("patients").document(task["patient_id"])

    # Update patient to "admitted" status
    patient_ref.update(
        {"status": "admitted", "admission.nurse_care_started_at": datetime.utcnow()}
    )
