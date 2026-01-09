"""
Agent HTTP Server for CareFlow Nexus Backend Integration
Exposes AI agents as HTTP endpoints that the backend can call
Matches the API contract expected by backend/app/services/agents.py
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from allocator_agent import BedAllocatorAgent
from communicator_agent import CommunicatorAgent
from config import config
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from memory_agent import MemoryAgent
from pydantic import BaseModel
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"agent_server_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CareFlow AI Agent Server",
    description="AI Agent Microservice for Hospital Bed Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances
firebase_service: Optional[FirebaseService] = None
gemini_service: Optional[GeminiService] = None
memory_agent: Optional[MemoryAgent] = None
bed_allocator_agent: Optional[BedAllocatorAgent] = None
communicator_agent: Optional[CommunicatorAgent] = None


# ==================== REQUEST/RESPONSE MODELS ====================


class BedAgentRequest(BaseModel):
    """Request model for bed assignment agent"""

    patient: Dict[str, Any]
    doctor_input: Dict[str, Any]
    available_beds: List[Dict[str, Any]]


class BedAgentResponse(BaseModel):
    """Response model for bed assignment agent"""

    recommended_bed_id: Optional[str]
    reason: str
    recommendations: List[Dict[str, Any]]
    confidence: int


class CleanerAgentRequest(BaseModel):
    """Request model for cleaner assignment agent"""

    bed_id: str
    available_cleaners: List[Dict[str, Any]]


class CleanerAgentResponse(BaseModel):
    """Response model for cleaner assignment agent"""

    selected_cleaner_id: Optional[str]
    reason: str


class NurseAgentRequest(BaseModel):
    """Request model for nurse assignment agent"""

    patient: Dict[str, Any]
    bed: Dict[str, Any]
    available_nurses: List[Dict[str, Any]]


class NurseAgentResponse(BaseModel):
    """Response model for nurse assignment agent"""

    selected_nurse_id: Optional[str]
    reason: str


# ==================== STARTUP/SHUTDOWN ====================


@app.on_event("startup")
async def startup_event():
    """Initialize all AI agents on server startup"""
    global \
        firebase_service, \
        gemini_service, \
        memory_agent, \
        bed_allocator_agent, \
        communicator_agent

    try:
        logger.info("=" * 60)
        logger.info("CareFlow AI Agent Server Starting...")
        logger.info("=" * 60)

        # Validate configuration
        logger.info("Validating configuration...")
        if not config.validate():
            raise Exception("Configuration validation failed")
        logger.info("✓ Configuration valid")

        # Initialize Firebase service
        logger.info("Initializing Firebase service...")
        firebase_service = FirebaseService(
            service_account_path=config.firebase.service_account_path
        )
        logger.info("✓ Firebase service initialized")

        # Initialize Gemini service
        logger.info("Initializing Gemini AI service...")
        gemini_service = GeminiService(
            api_key=config.gemini.api_key,
            model_name=config.gemini.model_name,
        )
        logger.info("✓ Gemini AI service initialized")

        # Initialize Memory Agent
        logger.info("Initializing Memory Agent...")
        memory_agent = MemoryAgent(
            firebase_service=firebase_service,
            gemini_service=gemini_service,
            refresh_interval=config.agent.state_refresh_interval,
        )
        await memory_agent.initialize()
        logger.info("✓ Memory Agent initialized")

        # Initialize Bed Allocator Agent
        logger.info("Initializing Bed Allocator Agent...")
        bed_allocator_agent = BedAllocatorAgent(
            firebase_service=firebase_service,
            gemini_service=gemini_service,
            memory_agent=memory_agent,
            rule_weight=config.agent.rule_weight,
        )
        logger.info("✓ Bed Allocator Agent initialized")

        # Initialize Communicator Agent
        logger.info("Initializing Communicator Agent...")
        communicator_agent = CommunicatorAgent(
            firebase_service=firebase_service,
            gemini_service=gemini_service,
            memory_agent=memory_agent,
            max_staff_workload=config.agent.max_staff_workload,
        )
        logger.info("✓ Communicator Agent initialized")

        logger.info("=" * 60)
        logger.info("✓ ALL AGENTS READY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    logger.info("Shutting down AI Agent Server...")


# ==================== HELPER FUNCTIONS ====================


def _extract_basic_requirements(doctor_input: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic requirements from doctor input"""
    diagnosis = doctor_input.get("diagnosis", "").lower()
    special_instructions = doctor_input.get("special_instructions", "").lower()

    combined_text = f"{diagnosis} {special_instructions}"

    requirements = {
        "needs_oxygen": any(
            word in combined_text for word in ["oxygen", "o2", "respiratory"]
        ),
        "needs_ventilator": any(
            word in combined_text for word in ["ventilator", "intubation"]
        ),
        "needs_cardiac_monitor": any(
            word in combined_text for word in ["cardiac", "heart", "monitor"]
        ),
        "needs_isolation": any(
            word in combined_text for word in ["isolation", "infectious", "contagious"]
        ),
    }

    return requirements


def _infer_severity(diagnosis: str) -> str:
    """Infer severity from diagnosis text"""
    diagnosis_lower = diagnosis.lower()

    if any(
        word in diagnosis_lower for word in ["critical", "severe", "emergency", "acute"]
    ):
        return "critical"
    elif any(word in diagnosis_lower for word in ["moderate", "significant"]):
        return "high"
    elif any(word in diagnosis_lower for word in ["mild", "minor"]):
        return "low"
    else:
        return "moderate"


# ==================== HEALTH CHECK ====================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agents_ready = all(
        [
            firebase_service is not None,
            gemini_service is not None,
            memory_agent is not None,
            bed_allocator_agent is not None,
            communicator_agent is not None,
        ]
    )

    return {
        "status": "healthy" if agents_ready else "initializing",
        "agents_ready": agents_ready,
        "timestamp": datetime.now().isoformat(),
    }


# ==================== AGENT ENDPOINTS ====================


@app.post("/agent/bed-assignment", response_model=BedAgentResponse)
async def call_bed_agent(request: BedAgentRequest):
    """
    Bed Assignment Agent Endpoint

    Returns bed recommendations based on patient diagnosis and available beds.
    Uses hybrid AI + rule-based scoring.

    Input:
    {
        "patient": {...},
        "doctor_input": {
            "diagnosis": "Pneumonia",
            "special_instructions": "Oxygen support"
        },
        "available_beds": [...]
    }

    Output:
    {
        "recommended_bed_id": "bed22",
        "reason": "Supports oxygen",
        "recommendations": [top 3 beds with scores],
        "confidence": 85
    }
    """
    try:
        if not bed_allocator_agent:
            raise HTTPException(status_code=503, detail="Agents not initialized")

        patient = request.patient
        doctor_input = request.doctor_input
        patient_id = patient.get("patient_id")

        logger.info(f"Bed assignment request for patient: {patient_id}")

        # Update patient with diagnosis information
        await firebase_service.update_patient(
            patient_id,
            {
                "diagnosis": doctor_input.get("diagnosis"),
                "severity": _infer_severity(doctor_input.get("diagnosis", "")),
                "requirements": _extract_basic_requirements(doctor_input),
            },
        )

        # Call Bed Allocator Agent
        result = await bed_allocator_agent.process({"patient_id": patient_id})

        if not result.get("success"):
            logger.warning(f"No suitable beds found for patient {patient_id}")
            return BedAgentResponse(
                recommended_bed_id=None,
                reason=result.get("message", "No suitable beds found"),
                recommendations=[],
                confidence=0,
            )

        data = result.get("data", {})
        recommendations = data.get("recommendations", [])

        # Format response according to API contract
        response = BedAgentResponse(
            recommended_bed_id=recommendations[0].get("bed_id")
            if recommendations
            else None,
            reason=recommendations[0].get("reasoning")
            if recommendations
            else "No beds available",
            recommendations=[
                {
                    "bed_id": rec.get("bed_id"),
                    "bed_number": rec.get("bed_number"),
                    "ward": rec.get("ward"),
                    "score": rec.get("score"),
                    "reasoning": rec.get("reasoning"),
                    "pros": rec.get("pros", []),
                    "cons": rec.get("cons", []),
                }
                for rec in recommendations[:3]  # Top 3
            ],
            confidence=data.get("confidence", 0),
        )

        logger.info(f"Bed assignment complete: {response.recommended_bed_id}")
        return response

    except Exception as e:
        logger.error(f"Error in bed agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/agent/cleaner-assignment", response_model=CleanerAgentResponse)
async def call_cleaner_agent(request: CleanerAgentRequest):
    """
    Cleaner Assignment Agent Endpoint

    Assigns a cleaner to prepare a bed.

    Input:
    {
        "bed_id": "bed22",
        "available_cleaners": [...]
    }

    Output:
    {
        "selected_cleaner_id": "c1",
        "reason": "Least workload"
    }
    """
    try:
        if not communicator_agent:
            raise HTTPException(status_code=503, detail="Agents not initialized")

        bed_id = request.bed_id
        available_cleaners = request.available_cleaners

        logger.info(f"Cleaner assignment request for bed: {bed_id}")

        # Get bed information
        bed = await firebase_service.get_bed(bed_id)
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")

        # Use Communicator Agent to assign staff
        task_data = {
            "task_type": "cleaning",
            "description": f"Clean bed {bed.get('bed_id')} in {bed.get('ward')}",
            "bed_id": bed_id,
            "priority": "high",
            "role": "cleaner",
        }

        result = await communicator_agent.process(
            {"type": "assign_staff", "task_data": task_data}
        )

        if result.get("success"):
            assignment = result.get("data", {})
            response = CleanerAgentResponse(
                selected_cleaner_id=assignment.get("staff_id"),
                reason=assignment.get(
                    "reasoning", "Selected based on workload and availability"
                ),
            )
        else:
            # Fallback: select first available cleaner
            if available_cleaners:
                response = CleanerAgentResponse(
                    selected_cleaner_id=available_cleaners[0].get("user_id"),
                    reason="First available cleaner",
                )
            else:
                response = CleanerAgentResponse(
                    selected_cleaner_id=None,
                    reason="No cleaners available",
                )

        logger.info(f"Cleaner assignment complete: {response.selected_cleaner_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cleaner agent: {e}")
        # Fallback
        if request.available_cleaners:
            return CleanerAgentResponse(
                selected_cleaner_id=request.available_cleaners[0].get("user_id"),
                reason=f"Fallback assignment due to error",
            )
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/agent/nurse-assignment", response_model=NurseAgentResponse)
async def call_nurse_agent(request: NurseAgentRequest):
    """
    Nurse Assignment Agent Endpoint

    Assigns a nurse to prepare a bed for a patient.

    Input:
    {
        "patient": {...},
        "bed": {...},
        "available_nurses": [...]
    }

    Output:
    {
        "selected_nurse_id": "n1",
        "reason": "ICU trained"
    }
    """
    try:
        if not communicator_agent:
            raise HTTPException(status_code=503, detail="Agents not initialized")

        patient = request.patient
        bed = request.bed
        available_nurses = request.available_nurses

        logger.info(
            f"Nurse assignment request for patient: {patient.get('patient_id')}"
        )

        # Use Communicator Agent to assign nurse
        task_data = {
            "task_type": "nursing",
            "description": f"Prepare bed {bed.get('bed_id')} for patient {patient.get('name')}",
            "bed_id": bed.get("bed_id"),
            "patient_id": patient.get("patient_id"),
            "priority": "high",
            "role": "nurse",
        }

        result = await communicator_agent.process(
            {"type": "assign_staff", "task_data": task_data}
        )

        if result.get("success"):
            assignment = result.get("data", {})
            response = NurseAgentResponse(
                selected_nurse_id=assignment.get("staff_id"),
                reason=assignment.get(
                    "reasoning", "Selected based on workload and specialization"
                ),
            )
        else:
            # Fallback
            if available_nurses:
                response = NurseAgentResponse(
                    selected_nurse_id=available_nurses[0].get("user_id"),
                    reason="First available nurse",
                )
            else:
                response = NurseAgentResponse(
                    selected_nurse_id=None,
                    reason="No nurses available",
                )

        logger.info(f"Nurse assignment complete: {response.selected_nurse_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in nurse agent: {e}")
        # Fallback
        if request.available_nurses:
            return NurseAgentResponse(
                selected_nurse_id=request.available_nurses[0].get("user_id"),
                reason=f"Fallback assignment",
            )
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ==================== MAIN ====================


if __name__ == "__main__":
    # Get port from environment or use default
    import os

    import uvicorn

    port = int(os.getenv("AGENT_SERVER_PORT", "9000"))

    logger.info(f"Starting Agent Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
