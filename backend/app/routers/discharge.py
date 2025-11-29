# app/routers/discharge.py
from fastapi import APIRouter, HTTPException
from app.db import supabase

router = APIRouter(tags=["discharge"])

@router.post("/patients/{patient_id}/request")
def request_discharge(patient_id: int):
    # 1) Check patient exists
    patient_res = supabase.table("patients").select("*").eq("id", patient_id).single().execute()
    patient = patient_res.data
    if not patient:
        raise HTTPException(404, "Patient not found")

    # Only patients under care can be discharged
    if patient["status"] != "under_care":
        raise HTTPException(400, "Discharge can only be requested when patient is under care")

    # 2) Fetch admission record to get bed_id
    admission_res = supabase.table("admissions").select("*").eq("patient_id", patient_id).single().execute()
    admission = admission_res.data
    if not admission:
        raise HTTPException(500, "Admission record missing")

    bed_id = admission.get("bed_id")
    if not bed_id:
        raise HTTPException(500, "Patient has no assigned bed")

    # 3) Update patient status
    supabase.table("patients").update({
        "status": "discharge_requested"
    }).eq("id", patient_id).execute()

    # 4) Create nurse task for discharge
    task_res = supabase.table("tasks").insert({
        "type": "nurse_assignment",
        "agent_role": "NURSE",
        "patient_id": patient_id,
        "bed_id": bed_id,
        "status": "pending"
    }).execute()
    task = task_res.data[0]

    return {
        "message": "Discharge requested",
        "patient": patient_id,
        "bed_id": bed_id,
        "task_created": task
    }
