# app/routers/patients.py
from fastapi import APIRouter, HTTPException
from app.db import supabase

router = APIRouter(tags=["patients"])

@router.post("/")
def create_patient(name: str):
    # create patient with default status pending_bed
    res = supabase.table("patients").insert({"name": name, "status": "pending_bed"}).execute()
    data = res.data
    if not data:
        raise HTTPException(500, "Failed to create patient")
    # res.data might be a list with one item
    return data[0] if isinstance(data, list) else data

@router.get("/")
def list_patients():
    return supabase.table("patients").select("*").order("id", desc=False).execute().data
