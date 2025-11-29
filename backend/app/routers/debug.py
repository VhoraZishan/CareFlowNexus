# app/routers/debug.py
from fastapi import APIRouter

router = APIRouter(tags=["debug"])

@router.get("/")
def debug_root():
    return {"debug": True}
