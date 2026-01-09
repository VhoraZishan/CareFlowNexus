from fastapi import HTTPException
from app.core.firebase import db

def get_user(user_id: str):
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        raise HTTPException(401, "Invalid user")
    return doc.to_dict()

def require_role(user_id: str, allowed: list[str]):
    user = get_user(user_id)
    if user["role"] not in allowed:
        raise HTTPException(403, "Forbidden")
    return user
