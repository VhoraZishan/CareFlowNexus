# app/routers/admissions.py
from fastapi import APIRouter, HTTPException
from app.db import supabase

router = APIRouter(tags=["admissions"])

@router.post("/patients/{patient_id}/admit")
def admit_patient(patient_id: int):
    # 1) Check if patient exists
    patient_res = supabase.table("patients").select("*").eq("id", patient_id).single().execute()
    patient = patient_res.data
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2) Allow only if patient is pending_bed
    if patient.get("status") != "pending_bed":
        raise HTTPException(status_code=400, detail="Patient cannot be admitted in current state")

    # 3) Create admission record (admissions.status is TEXT in DB; use 'awaiting_cleaning' to indicate flow started)
    admission_res = supabase.table("admissions").insert({
        "patient_id": patient_id,
        "bed_id": None,
        "status": "awaiting_cleaning"
    }).execute()
    admission = admission_res.data[0] if admission_res.data else None
    if not admission:
        raise HTTPException(500, "Failed to create admission")

    # 4) Create task for BED agent to coordinate bed assignment
    task_res = supabase.table("tasks").insert({
        "type": "bed_assignment",
        "agent_role": "BED",
        "patient_id": patient_id,
        "bed_id": None,
        "status": "pending"
    }).execute()
    task = task_res.data[0] if task_res.data else None
    if not task:
        raise HTTPException(500, "Failed to create master task")

    return {
        "message": "Admission started",
        "patient": patient,
        "admission": admission,
        "task_created": task
    }
