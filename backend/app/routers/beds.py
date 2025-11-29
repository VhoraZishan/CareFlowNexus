# app/routers/beds.py
from fastapi import APIRouter, HTTPException
from app.db import supabase

router = APIRouter(tags=["beds"])

@router.get("/")
def list_beds():
    return supabase.table("beds").select("*").order("id", desc=False).execute().data

@router.get("/available")
def list_available_beds():
    return supabase.table("beds").select("*").eq("status", "available").order("id", desc=False).execute().data
