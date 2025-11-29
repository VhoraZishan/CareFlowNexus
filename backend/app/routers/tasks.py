# app/routers/tasks.py
from fastapi import APIRouter, HTTPException, Body
from app.db import supabase

router = APIRouter(tags=["tasks"])

@router.get("/")
def list_tasks():
    return supabase.table("tasks").select("*").order("created_at", desc=False).execute().data

@router.post("/")
def create_task(
    type: str = Body(...),
    agent_role: str = Body(None),
    patient_id: int = Body(None),
    bed_id: int = Body(None),
    target_role: str = Body(None)
):
    payload = {
        "type": type,
        "patient_id": patient_id,
        "bed_id": bed_id,
        "status": "pending"
    }

    if agent_role:
        payload["agent_role"] = agent_role

    if target_role:
        payload["target_role"] = target_role

    res = supabase.table("tasks").insert(payload).execute()

    if not res.data:
        raise HTTPException(500, "Failed to create task")

    # Normalize return: always return a single task dict
    return res.data[0] if isinstance(res.data, list) else res.data
