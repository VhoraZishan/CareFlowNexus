"""
CareFlow Nexus - FastAPI Backend API
Exposes AI agents through REST API endpoints with Swagger UI documentation
"""

from datetime import datetime
from typing import Dict, List, Optional

from allocator_agent import BedAllocatorAgent
from communicator_agent import CommunicatorAgent
from config import config
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from memory_agent import MemoryAgent
from pydantic import BaseModel, Field
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService

# Initialize FastAPI app
app = FastAPI(
    title="CareFlow Nexus API",
    description="AI-Powered Hospital Bed Management System with Gemini 2.5 Flash",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for services and agents
firebase_service: Optional[FirebaseService] = None
gemini_service: Optional[GeminiService] = None
memory_agent: Optional[MemoryAgent] = None
bed_allocator_agent: Optional[BedAllocatorAgent] = None
communicator_agent: Optional[CommunicatorAgent] = None


# ==================== REQUEST/RESPONSE MODELS ====================


class LoginRequest(BaseModel):
    username: str = Field(..., example="doctor1")
    password: str = Field(..., example="doc123")


class LoginResponse(BaseModel):
    user_id: str
    role: str
    username: str


class PatientCreateRequest(BaseModel):
    user_id: str = Field(..., example="u_recep_01")
    name: str = Field(..., example="John Doe")
    age: int = Field(..., example=52, ge=0, le=150)
    gender: str = Field(..., example="male")
    medical_history: List[str] = Field(default=[], example=["diabetes"])
    special_needs: List[str] = Field(default=[], example=["wheelchair"])


class PatientCreateResponse(BaseModel):
    patient_id: str
    status: str


class DiagnosisRequest(BaseModel):
    user_id: str = Field(..., example="u_doc_01")
    diagnosis: str = Field(..., example="Pneumonia")
    special_instructions: str = Field(..., example="Oxygen support")


class BedRecommendation(BaseModel):
    bed_id: str
    bed_number: str
    ward: str
    score: float
    reasoning: str
    pros: List[str]
    cons: List[str]


class DiagnosisResponse(BaseModel):
    recommended_beds: List[BedRecommendation]
    confidence: int
    status: str


class ConfirmBedRequest(BaseModel):
    user_id: str = Field(..., example="u_recep_01")
    bed_id: str = Field(..., example="bed_icu_01")
    confirm: bool = Field(default=True)


class ConfirmBedResponse(BaseModel):
    status: str
    bed_number: str
    tasks_created: int


class TaskResponse(BaseModel):
    task_id: str
    type: str
    role: str
    patient_id: Optional[str]
    bed_id: str
    assigned_to: str
    status: str
    created_at: str


class TaskActionRequest(BaseModel):
    user_id: str


# ==================== STARTUP/SHUTDOWN ====================


@app.on_event("startup")
async def startup_event():
    """Initialize all services and agents on startup"""
    global \
        firebase_service, \
        gemini_service, \
        memory_agent, \
        bed_allocator_agent, \
        communicator_agent

    try:
        print("=" * 60)
        print("Starting CareFlow Nexus API Server")
        print("=" * 60)

        # Initialize Firebase
        print("Initializing Firebase...")
        firebase_service = FirebaseService(config.firebase.service_account_path)
        print("OK Firebase initialized")

        # Initialize Gemini
        print("Initializing Gemini AI...")
        gemini_service = GeminiService(config.gemini.api_key, config.gemini.model_name)
        print("OK Gemini initialized")

        # Initialize Memory Agent
        print("Initializing Memory Agent...")
        memory_agent = MemoryAgent(firebase_service, gemini_service)
        await memory_agent.initialize()
        print("OK Memory Agent initialized")

        # Initialize Bed Allocator Agent
        print("Initializing Bed Allocator Agent...")
        bed_allocator_agent = BedAllocatorAgent(
            firebase_service, gemini_service, memory_agent, config.agent.rule_weight
        )
        print("OK Bed Allocator Agent initialized")

        # Initialize Communicator Agent
        print("Initializing Communicator Agent...")
        communicator_agent = CommunicatorAgent(
            firebase_service,
            gemini_service,
            memory_agent,
            config.agent.max_staff_workload,
        )
        print("OK Communicator Agent initialized")

        print("=" * 60)
        print("OK All agents initialized successfully")
        print("API Server ready at http://0.0.0.0:8000")
        print("Swagger Docs: http://0.0.0.0:8000/docs")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR Failed to initialize: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down CareFlow Nexus API Server...")


# ==================== HEALTH CHECK ====================


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "memory_agent": memory_agent is not None,
            "bed_allocator_agent": bed_allocator_agent is not None,
            "communicator_agent": communicator_agent is not None,
        },
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CareFlow Nexus API",
        "version": "1.0.0",
        "description": "AI-Powered Hospital Bed Management System",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


# ==================== AUTHENTICATION ====================


@app.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Validate user credentials and return user role

    No JWT - just validates and returns user info
    """
    try:
        # Get user from Firebase
        users = (
            firebase_service.db.collection("users")
            .where("username", "==", request.username)
            .stream()
        )

        user_list = [doc.to_dict() for doc in users]

        if not user_list:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user = user_list[0]

        # Simple password check (no hashing as per requirements)
        if user.get("password") != request.password:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not user.get("active", True):
            raise HTTPException(status_code=403, detail="User account is inactive")

        return LoginResponse(
            user_id=user["user_id"], role=user["role"], username=user["username"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ==================== PATIENT ENDPOINTS ====================


@app.post("/patients", response_model=PatientCreateResponse, tags=["Patients"])
async def create_patient(request: PatientCreateRequest):
    """
    Create new patient (Receptionist only)

    Creates a patient record in the system
    """
    try:
        # TODO: Verify user_id has receptionist role

        patient_data = {
            "name": request.name,
            "age": request.age,
            "gender": request.gender,
            "medical_history": request.medical_history,
            "special_needs": request.special_needs,
            "status": "created",
            "created_by": request.user_id,
            "created_at": datetime.now().isoformat(),
            "admission": None,
        }

        patient_id = await firebase_service.create_patient(patient_data)

        if not patient_id:
            raise HTTPException(status_code=500, detail="Failed to create patient")

        return PatientCreateResponse(patient_id=patient_id, status="created")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients", tags=["Patients"])
async def get_patients(user_id: str):
    """
    Get list of patients based on user role

    - Receptionist: all patients
    - Doctor: created, admitted patients
    - Nurse: assigned patients only
    """
    try:
        # Get user role
        user_doc = firebase_service.db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")

        role = user_doc.to_dict().get("role")

        # Get all patients
        patients = await firebase_service.get_all_patients()

        # Filter based on role
        if role == "receptionist":
            return patients
        elif role == "doctor":
            return [p for p in patients if p.get("status") in ["created", "admitted"]]
        elif role == "nurse":
            # Filter by assigned nurse
            return [
                p for p in patients if p.get("admission", {}).get("nurse_id") == user_id
            ]
        else:
            return []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients/{patient_id}", tags=["Patients"])
async def get_patient(patient_id: str, user_id: str):
    """Get specific patient details"""
    try:
        patient = await firebase_service.get_patient(patient_id)

        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # TODO: Apply role-based field filtering

        return patient

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADMISSION ENDPOINTS ====================


@app.post(
    "/patients/{patient_id}/admission",
    response_model=DiagnosisResponse,
    tags=["Admission"],
)
async def submit_diagnosis(patient_id: str, request: DiagnosisRequest):
    """
    Doctor submits diagnosis and gets bed recommendations from AI

    Triggers the Bed Allocator Agent (50% rule-based + 50% AI)
    """
    try:
        # Get patient
        patient = await firebase_service.get_patient(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Update patient with diagnosis
        await firebase_service.update_patient(
            patient_id,
            {
                "status": "pending_confirmation",
                "admission": {
                    "doctor_id": request.user_id,
                    "diagnosis": request.diagnosis,
                    "special_instructions": request.special_instructions,
                    "recommended_bed_id": None,
                    "confirmed_bed_id": None,
                    "nurse_id": None,
                    "admitted_at": None,
                },
            },
        )

        # Call Bed Allocator Agent
        allocation_result = await bed_allocator_agent.process(
            {"patient_id": patient_id}
        )

        if not allocation_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=allocation_result.get("message", "Bed allocation failed"),
            )

        data = allocation_result.get("data", {})
        recommendations = data.get("recommendations", [])

        # Format recommendations
        bed_recommendations = [
            BedRecommendation(
                bed_id=rec.get("bed_id"),
                bed_number=rec.get("bed_number"),
                ward=rec.get("ward"),
                score=rec.get("score"),
                reasoning=rec.get("reasoning", ""),
                pros=rec.get("pros", []),
                cons=rec.get("cons", []),
            )
            for rec in recommendations
        ]

        # Store recommended bed in patient record
        if bed_recommendations:
            await firebase_service.update_patient(
                patient_id,
                {"admission.recommended_bed_id": bed_recommendations[0].bed_id},
            )

        return DiagnosisResponse(
            recommended_beds=bed_recommendations,
            confidence=data.get("confidence", 0),
            status="pending_confirmation",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/patients/{patient_id}/confirm-bed",
    response_model=ConfirmBedResponse,
    tags=["Admission"],
)
async def confirm_bed(patient_id: str, request: ConfirmBedRequest):
    """
    Receptionist confirms bed assignment

    Triggers the Communicator Agent to create tasks for staff
    """
    try:
        if not request.confirm:
            return ConfirmBedResponse(
                status="cancelled", bed_number="", tasks_created=0
            )

        # Get patient and bed
        patient = await firebase_service.get_patient(patient_id)
        bed = await firebase_service.get_bed(request.bed_id)

        if not patient or not bed:
            raise HTTPException(status_code=404, detail="Patient or bed not found")

        # Assign bed to patient
        await firebase_service.assign_bed_to_patient(request.bed_id, patient_id)

        # Update patient status
        await firebase_service.update_patient(
            patient_id,
            {
                "status": "admitted",
                "admission.confirmed_bed_id": request.bed_id,
                "admission.admitted_at": datetime.now().isoformat(),
            },
        )

        # Create tasks using Communicator Agent
        workflow_result = await communicator_agent.process(
            {
                "type": "initiate_workflow",
                "workflow_type": "bed_assignment",
                "context": {"patient_id": patient_id, "bed_id": request.bed_id},
            }
        )

        tasks_created = 0
        if workflow_result.get("success"):
            tasks_created = len(
                workflow_result.get("data", {}).get("tasks_created", [])
            )

        return ConfirmBedResponse(
            status="admitted",
            bed_number=bed.get("bed_id", ""),
            tasks_created=tasks_created,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TASK ENDPOINTS ====================


@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def get_tasks(user_id: str):
    """
    Get tasks assigned to user (Cleaner or Nurse)
    """
    try:
        # Get tasks assigned to this user
        tasks = (
            firebase_service.db.collection("tasks")
            .where("assigned_to", "==", user_id)
            .stream()
        )

        task_list = []
        for doc in tasks:
            task = doc.to_dict()
            task_list.append(
                TaskResponse(
                    task_id=doc.id,
                    type=task.get("type", ""),
                    role=task.get("role", ""),
                    patient_id=task.get("patient_id"),
                    bed_id=task.get("bed_id", ""),
                    assigned_to=task.get("assigned_to", ""),
                    status=task.get("status", ""),
                    created_at=str(task.get("created_at", "")),
                )
            )

        return task_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{task_id}/accept", tags=["Tasks"])
async def accept_task(task_id: str, request: TaskActionRequest):
    """Staff member accepts assigned task"""
    try:
        # Update task status to accepted (in_progress)
        success = await firebase_service.update_task_status(
            task_id, "accepted", "Task accepted by staff"
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to accept task")

        return {"status": "accepted", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/{task_id}/complete", tags=["Tasks"])
async def complete_task(task_id: str, request: TaskActionRequest):
    """Staff member marks task as completed"""
    try:
        # Update task status to completed
        success = await firebase_service.update_task_status(
            task_id, "completed", "Task completed by staff"
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to complete task")

        return {"status": "completed", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AGENT ENDPOINTS (for testing) ====================


@app.get("/agent/beds", tags=["AI Agents"])
async def get_available_beds(ward: Optional[str] = None):
    """Get available beds from Memory Agent"""
    try:
        filters = {}
        if ward:
            filters["ward"] = ward

        response = await memory_agent.process(
            {"type": "get_available_beds", "filters": filters}
        )

        return response.get("data", [])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/state", tags=["AI Agents"])
async def get_system_state():
    """Get complete hospital state from Memory Agent"""
    try:
        response = await memory_agent.process({"type": "get_system_state"})
        return response.get("data", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/analyze", tags=["AI Agents"])
async def analyze_state():
    """Run AI analysis on current hospital state"""
    try:
        response = await memory_agent.process({"type": "analyze_state"})
        return response.get("data", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ERROR HANDLERS ====================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
