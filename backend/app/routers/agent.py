# app/routers/agent.py
from fastapi import APIRouter, HTTPException, Body
from app.db import supabase

router = APIRouter(tags=["agent"])

# Allowed agent roles according to your DB enum
ALLOWED_AGENT_ROLES = {"MASTER", "BED", "CLEANER", "NURSE"}

@router.get("/tasks")
def get_agent_tasks(role: str):
    role = role.upper()
    if role not in ALLOWED_AGENT_ROLES:
        raise HTTPException(400, f"Invalid agent role: {role}")
    res = supabase.table("tasks").select("*").eq("agent_role", role).eq("status", "pending").order("created_at", desc=False).execute()
    return res.data

@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, payload: dict = Body(...)):
    """
    Agents call this to mark a task completed and optionally provide:
      - bed_id (for bed_assignment tasks by BED agent)
      - next_task (dict) to create (if MASTER creates next task)
      - patient_status to update patient
      - bed_status to update bed (if provided)
    This implements the doc workflow:
      MASTER (creates BED task) -> BED (chooses bed) -> CLEANER -> NURSE
    """
    # fetch task
    task_res = supabase.table("tasks").select("*").eq("id", task_id).single().execute()
    task = task_res.data
    if not task:
        raise HTTPException(404, "Task not found")

    task_type = task.get("type")
    agent_role = task.get("agent_role")
    patient_id = task.get("patient_id")
    bed_id = task.get("bed_id")

    # Mark current task completed (we will update after validations)
    # We'll perform specific logic per task_type:
    next_task = None

    # MASTER completes: expected to provide next_task in payload to enqueue a BED-level task
    if agent_role == "MASTER" and task_type == "bed_assignment":
        # MASTER can optionally provide a next_task dict to create a BED task.
        if "next_task" in payload:
            nt = payload["next_task"]
            # minimal validation
            if "type" not in nt or "agent_role" not in nt:
                raise HTTPException(400, "next_task must contain type and agent_role")
            # create the next task (likely type 'bed_assignment' with agent_role 'BED')
            created = supabase.table("tasks").insert({
                "type": nt["type"],
                "agent_role": nt["agent_role"].upper(),
                "patient_id": patient_id,
                "bed_id": nt.get("bed_id"),
                "status": "pending"
            }).execute().data
            next_task = created[0] if created else None

        # finally mark master task completed
        supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()
        return {"message": "Master task completed", "next_task": next_task}

    # BED agent completes bed_assignment: must supply bed_id
    if agent_role == "BED" and task_type == "bed_assignment":
        if "bed_id" not in payload:
            raise HTTPException(400, "bed_id required for bed_assignment by BED agent")

        bed_id = payload["bed_id"]
        # validate bed exists and is available
        bed_res = supabase.table("beds").select("*").eq("id", bed_id).single().execute()
        bed = bed_res.data
        if not bed:
            raise HTTPException(400, "Bed not found")
        if bed.get("status") != "available":
            raise HTTPException(400, "Bed not available")

        # link bed to admission, set admission.status to 'assigned', update patient.status to 'assigned'
        supabase.table("admissions").update({
            "bed_id": bed_id,
            "status": "assigned"
        }).eq("patient_id", patient_id).execute()

        supabase.table("patients").update({
            "status": "assigned"
        }).eq("id", patient_id).execute()

        # mark bed pending cleaning
        supabase.table("beds").update({
            "status": "pending_cleaning"
        }).eq("id", bed_id).execute()

        # complete current BED task
        supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

        # create next task: cleaning for CLEANER
        created = supabase.table("tasks").insert({
            "type": "cleaning",
            "agent_role": "CLEANER",
            "patient_id": patient_id,
            "bed_id": bed_id,
            "status": "pending"
        }).execute().data
        next_task = created[0] if created else None

        return {"message": "Bed assigned; cleaning task created", "next_task": next_task}

    # CLEANER completes cleaning -> mark bed available and create nurse_assignment
    if agent_role == "CLEANER" and task_type == "cleaning":
        bed_id = task.get("bed_id")
        if not bed_id:
            raise HTTPException(400, "Cleaning task has no bed_id")

        # mark bed ready (available)
        supabase.table("beds").update({"status": "available"}).eq("id", bed_id).execute()

        # mark cleaning task completed
        supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

        # create nurse assignment task
        created = supabase.table("tasks").insert({
            "type": "nurse_assignment",
            "agent_role": "NURSE",
            "patient_id": patient_id,
            "bed_id": bed_id,
            "status": "pending"
        }).execute().data
        next_task = created[0] if created else None

        return {"message": "Cleaning completed; nurse assignment created", "next_task": next_task}
    
        # CLEANER completes post_discharge_cleaning -> bed becomes available
    if agent_role == "CLEANER" and task_type == "post_discharge_cleaning":
        bed_id = task.get("bed_id")
        if not bed_id:
            raise HTTPException(400, "Post discharge cleaning task has no bed_id")

        # Mark bed as fully available again
        supabase.table("beds").update({"status": "available"}).eq("id", bed_id).execute()

        # Complete the cleaning task
        supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

        return {
            "message": "Post-discharge cleaning completed; bed available",
            "next_task": None
        }


    # NURSE completes nurse_assignment -> patient under care, bed occupied
        # NURSE completes nurse_assignment -> Admission OR Discharge
    if agent_role == "NURSE" and task_type == "nurse_assignment":
        bed_id = task.get("bed_id")
        if not bed_id:
            raise HTTPException(400, "Nurse assignment has no bed_id")

        # Fetch patient to know context
        patient_res = supabase.table("patients").select("*").eq("id", patient_id).single().execute()
        patient = patient_res.data
        if not patient:
            raise HTTPException(404, "Patient not found")

        current_status = patient["status"]

        # -------------------------
        # ADMISSION CASE
        # -------------------------
        if current_status == "assigned":
            supabase.table("patients").update({"status": "under_care"}).eq("id", patient_id).execute()
            supabase.table("beds").update({"status": "occupied"}).eq("id", bed_id).execute()
            supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

            return {
                "message": "Nurse completed admission; patient under care",
                "next_task": None
            }

        # -------------------------
        # DISCHARGE CASE
        # -------------------------
        if current_status == "discharge_requested":
            # Update patient status
            supabase.table("patients").update({"status": "discharged"}).eq("id", patient_id).execute()

            # Mark bed pending post-discharge cleaning
            supabase.table("beds").update({"status": "pending_cleaning"}).eq("id", bed_id).execute()

            # Finish current nurse task
            supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

            # Create next cleaning task
            next_task_data = supabase.table("tasks").insert({
                "type": "post_discharge_cleaning",
                "agent_role": "CLEANER",
                "patient_id": patient_id,
                "bed_id": bed_id,
                "status": "pending"
            }).execute().data[0]

            return {
                "message": "Nurse completed discharge; cleaner task created",
                "next_task": next_task_data
            }

        # Unknown status = error
        raise HTTPException(400, f"Invalid patient status '{current_status}' for nurse_assignment")


    # Generic fallback: allow updating patient_status/bed_status or creating next_task
    # Update patient status if provided
    if "patient_status" in payload:
        supabase.table("patients").update({"status": payload["patient_status"]}).eq("id", patient_id).execute()

    if "bed_status" in payload and payload.get("bed_id"):
        supabase.table("beds").update({"status": payload["bed_status"]}).eq("id", payload["bed_id"]).execute()

    if "next_task" in payload:
        nt = payload["next_task"]
        if "type" in nt and "agent_role" in nt:
            created = supabase.table("tasks").insert({
                "type": nt["type"],
                "agent_role": nt["agent_role"].upper(),
                "patient_id": patient_id,
                "bed_id": nt.get("bed_id"),
                "status": "pending"
            }).execute().data
            next_task = created[0] if created else None

    # complete the current task
    supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

    return {"message": "Task completed (generic)", "next_task": next_task}
