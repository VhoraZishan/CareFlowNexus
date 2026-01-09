from fastapi import APIRouter
from app.models.schemas import TaskActionRequest, TaskCompleteRequest
from app.services.role_guard import require_role
from app.core.firebase import db
from app.services.agents import call_cleaner_agent
from app.services.tasks import create_task
from datetime import datetime

router = APIRouter(prefix="/tasks")

@router.get("")
def get_tasks(user_id: str):
    require_role(user_id, ["cleaner", "nurse"])

    tasks = []
    for doc in db.collection("tasks").where("assigned_to", "==", user_id).stream():
        tasks.append(doc.to_dict())

    return tasks

@router.post("/{task_id}/accept")
def accept_task(task_id: str, data: TaskActionRequest):
    require_role(data.user_id, ["cleaner", "nurse"])

    db.collection("tasks").document(task_id).update({
        "status": "accepted"
    })
    return {"status": "accepted"}

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
    task_ref.update({
        "status": "completed",
        "completed_at": datetime.utcnow(),
        "notes": data.notes
    })

    # BRANCH LOGIC
    if task["type"] == "discharge_nursing":
        _handle_nurse_discharge_completion(task)

    elif task["type"] == "cleaning":
        _handle_cleaning_completion(task)

    return {"status": "completed"}

def _handle_nurse_discharge_completion(task):
    patient_ref = db.collection("patients").document(task["patient_id"])
    patient = patient_ref.get().to_dict()

    # Update patient
    patient_ref.update({
        "status": "discharged",
        "discharge.completed_at": datetime.utcnow()
    })

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
        assigned_to=cleaner_id
    )


def _handle_cleaning_completion(task):
    # Free bed
    db.collection("beds").document(task["bed_id"]).update({
        "occupied": False,
        "current_patient_id": None
    })
