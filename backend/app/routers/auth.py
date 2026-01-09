from fastapi import APIRouter, HTTPException
from app.core.firebase import db
from app.models.schemas import LoginRequest

router = APIRouter(prefix="/auth")

@router.post("/login")
def login(data: LoginRequest):
    users = db.collection("users") \
        .where("username", "==", data.username) \
        .where("password", "==", data.password) \
        .limit(1).stream()

    for user in users:
        u = user.to_dict()
        return {"user_id": u["user_id"], "role": u["role"]}

    raise HTTPException(401, "Invalid credentials")
