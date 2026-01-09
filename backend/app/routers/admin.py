from app.core.firebase import db
from fastapi import APIRouter, HTTPException

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
        response.append(
            {
                "bed_id": doc.id,
                "ward": bed.get("ward"),
                "features": bed.get("features", []),
                "occupied": bed.get("occupied", False),
                "current_patient_id": bed.get("current_patient_id"),
            }
        )

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
        response.append(
            {
                "task_id": doc.id,
                "type": task.get("type"),
                "role": task.get("role"),
                "patient_id": task.get("patient_id"),
                "bed_id": task.get("bed_id"),
                "assigned_to": task.get("assigned_to"),
                "status": task.get("status"),
                "created_at": task.get("created_at"),
            }
        )

    return response


# -------------------------------------------------
# GET ALL NURSES
# -------------------------------------------------
@router.get("/nurses")
def get_all_nurses(user_id: str):
    """
    Admin-only: Returns all nurses with their detailed profiles
    """
    _validate_admin(user_id)

    nurses_ref = db.collection("users").where("role", "==", "nurse").stream()
    response = []

    for doc in nurses_ref:
        nurse = doc.to_dict()
        response.append(
            {
                "user_id": doc.id,
                "name": nurse.get("name"),
                "email": nurse.get("email"),
                "phone": nurse.get("phone"),
                "active": nurse.get("active"),
                "age": nurse.get("age"),
                "gender": nurse.get("gender"),
                "experience_years": nurse.get("experience_years"),
                "specialties": nurse.get("specialties", []),
                "certifications": nurse.get("certifications", []),
                "skills": nurse.get("skills", {}),
                "department": nurse.get("department"),
                "shift_preference": nurse.get("shift_preference"),
                "languages": nurse.get("languages", []),
                "max_patients": nurse.get("max_patients"),
                "current_patients": nurse.get("current_patients"),
                "availability": nurse.get("availability", {}),
                "notes": nurse.get("notes", ""),
            }
        )

    return response


# -------------------------------------------------
# GET ALL CLEANERS
# -------------------------------------------------
@router.get("/cleaners")
def get_all_cleaners(user_id: str):
    """
    Admin-only: Returns all cleaners with their detailed profiles
    """
    _validate_admin(user_id)

    cleaners_ref = db.collection("users").where("role", "==", "cleaner").stream()
    response = []

    for doc in cleaners_ref:
        cleaner = doc.to_dict()
        response.append(
            {
                "user_id": doc.id,
                "name": cleaner.get("name"),
                "email": cleaner.get("email"),
                "phone": cleaner.get("phone"),
                "active": cleaner.get("active"),
                "age": cleaner.get("age"),
                "gender": cleaner.get("gender"),
                "experience_years": cleaner.get("experience_years"),
                "specialties": cleaner.get("specialties", []),
                "certifications": cleaner.get("certifications", []),
                "skills": cleaner.get("skills", {}),
                "clearance_level": cleaner.get("clearance_level"),
                "equipment_certified": cleaner.get("equipment_certified", []),
                "department_expertise": cleaner.get("department_expertise", []),
                "shift_preference": cleaner.get("shift_preference"),
                "languages": cleaner.get("languages", []),
                "average_room_time": cleaner.get("average_room_time"),
                "current_tasks": cleaner.get("current_tasks"),
                "max_tasks_per_shift": cleaner.get("max_tasks_per_shift"),
                "availability": cleaner.get("availability", {}),
                "notes": cleaner.get("notes", ""),
            }
        )

    return response
