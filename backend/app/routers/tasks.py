from fastapi import APIRouter
from app.models.schemas import TaskActionRequest
from app.services.role_guard import require_role
from app.core.firebase import db

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
