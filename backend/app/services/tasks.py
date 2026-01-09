from app.core.firebase import db
from datetime import datetime
import uuid

def create_task(
    task_type: str,
    role: str,
    patient_id: str,
    bed_id: str,
    assigned_to: str
):
    task_id = str(uuid.uuid4())

    task = {
        "task_id": task_id,
        "type": task_type,          # cleaning | nursing
        "role": role,               # cleaner | nurse
        "patient_id": patient_id,
        "bed_id": bed_id,
        "assigned_to": assigned_to,
        "status": "assigned",
        "created_at": datetime.utcnow(),
        "completed_at": None
    }

    db.collection("tasks").document(task_id).set(task)
    return task
