from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class CreatePatientRequest(BaseModel):
    user_id: str
    name: str
    age: int
    gender: str
    medical_history: List[str]
    special_needs: List[str]

class AdmissionRequest(BaseModel):
    user_id: str
    diagnosis: str
    special_instructions: str

class ConfirmBedRequest(BaseModel):
    user_id: str
    bed_id: str
    confirm: Optional[bool] = True

class TaskActionRequest(BaseModel):
    user_id: str

class DischargeRequest(BaseModel):
    user_id: str
    discharge_notes: str

class TaskCompleteRequest(BaseModel):
    user_id: str
    notes: str | None = None
