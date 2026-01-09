from fastapi import APIRouter, HTTPException
from app.core.firebase import db

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


def _validate_admin(user_id: str):
    user_ref = db.collection("users").document(user_id).get()
    if not user_ref.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user = user_ref.to_dict()
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


# -------------------------------------------------
# GET ALL BEDS
# -------------------------------------------------
@router.get("/beds")
def get_all_beds(user_id: str):
    """
    Admin-only: Returns all beds and their current status
    """
    _validate_admin(user_id)

    beds_ref = db.collection("beds").stream()
    response = []

    for doc in beds_ref:
        bed = doc.to_dict()
        response.append({
            "bed_id": doc.id,
            "ward": bed.get("ward"),
            "features": bed.get("features", []),
            "occupied": bed.get("occupied", False),
            "current_patient_id": bed.get("current_patient_id")
        })

    return response


# -------------------------------------------------
# GET ALL TASKS
# -------------------------------------------------
@router.get("/tasks")
def get_all_tasks(user_id: str):
    """
    Admin-only: Returns all tasks in the system
    """
    _validate_admin(user_id)

    tasks_ref = db.collection("tasks").stream()
    response = []

    for doc in tasks_ref:
        task = doc.to_dict()
        response.append({
            "task_id": doc.id,
            "type": task.get("type"),
            "role": task.get("role"),
            "patient_id": task.get("patient_id"),
            "bed_id": task.get("bed_id"),
            "assigned_to": task.get("assigned_to"),
            "status": task.get("status"),
            "created_at": task.get("created_at")
        })

    return response
