"""
CareFlow Nexus - Pure Agent Server (No Database Access)
============================================================

STRICT REQUIREMENTS:
- Agents ONLY communicate with backend server
- Agents NEVER read or write to database
- Agents receive ALL data from backend in request payload
- Agents return ONLY recommendations as JSON
- Agents are stateless and deterministic

Base URL: http://localhost:9000/agent
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    title="CareFlow AI Agent Server (Pure)",
    description="Stateless AI Agents - No Database Access",
    version="2.0.0",
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


# ==================== REQUEST/RESPONSE MODELS ====================


class BedAgentRequest(BaseModel):
    """Bed assignment agent request - backend provides ALL data"""

    patient: Dict[str, Any]
    doctor_input: Dict[str, Any]
    available_beds: List[Dict[str, Any]]


class BedAgentResponse(BaseModel):
    """Bed assignment agent response - STRICT CONTRACT"""

    recommended_bed_id: Optional[str]
    reason: str


class CleanerAgentRequest(BaseModel):
    """Cleaner assignment agent request"""

    bed_id: str
    context: str  # "pre_admission" | "post_discharge"
    available_cleaners: List[Dict[str, Any]]


class CleanerAgentResponse(BaseModel):
    """Cleaner assignment agent response - STRICT CONTRACT"""

    selected_cleaner_id: Optional[str]
    reason: str


class NurseAgentRequest(BaseModel):
    """Nurse assignment agent request"""

    patient: Dict[str, Any]
    bed: Dict[str, Any]
    available_nurses: List[Dict[str, Any]]


class NurseAgentResponse(BaseModel):
    """Nurse assignment agent response - STRICT CONTRACT"""

    selected_nurse_id: Optional[str]
    reason: str


# ==================== HELPER FUNCTIONS (PURE COMPUTATION) ====================


def extract_requirements_from_diagnosis(
    diagnosis: str, instructions: str
) -> Dict[str, bool]:
    """
    Extract medical requirements from diagnosis text
    Pure function - no external dependencies
    """
    combined_text = f"{diagnosis} {instructions}".lower()

    return {
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
            word in combined_text
            for word in ["isolation", "infectious", "contagious", "covid", "tb"]
        ),
        "needs_icu": any(
            word in combined_text for word in ["icu", "critical", "intensive"]
        ),
    }


def score_bed_match(
    bed: Dict[str, Any], requirements: Dict[str, bool], patient: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Score how well a bed matches patient requirements
    Pure function - deterministic scoring
    """
    score = 0
    reasoning_parts = []
    pros = []
    cons = []

    bed_features = bed.get("features", [])
    bed_features_lower = [f.lower() for f in bed_features]
    ward = bed.get("ward", "").lower()

    # Check critical requirements
    if requirements.get("needs_oxygen"):
        if "oxygen" in bed_features_lower:
            score += 40
            pros.append("Has oxygen support")
        else:
            score -= 30
            cons.append("No oxygen support")

    if requirements.get("needs_isolation"):
        if "isolation" in ward or "isolation" in bed_features_lower:
            score += 40
            pros.append("Isolation ward")
        else:
            score -= 30
            cons.append("Not in isolation ward")

    if requirements.get("needs_icu"):
        if "icu" in ward or "intensive" in ward:
            score += 50
            pros.append("ICU bed")
        elif "general" in ward:
            score -= 20
            cons.append("General ward may not be suitable")

    if requirements.get("needs_ventilator"):
        if "ventilator" in bed_features_lower:
            score += 45
            pros.append("Ventilator available")
        else:
            score -= 35
            cons.append("No ventilator")

    if requirements.get("needs_cardiac_monitor"):
        if "cardiac" in bed_features_lower or "monitor" in bed_features_lower:
            score += 30
            pros.append("Cardiac monitoring")
        else:
            cons.append("No cardiac monitor")

    # Bonus points for additional features
    if bed_features:
        score += len(bed_features) * 5
        if len(bed_features) > 2:
            pros.append(f"{len(bed_features)} features available")

    # Ward appropriateness
    patient_age = patient.get("age", 0)
    if patient_age > 65 and "geriatric" in ward:
        score += 20
        pros.append("Age-appropriate ward")
    elif patient_age < 18 and "pediatric" in ward:
        score += 20
        pros.append("Pediatric ward")

    # Normalize score to 0-100
    score = max(0, min(100, score))

    # Generate reasoning
    if score >= 70:
        reasoning = f"Excellent match for patient requirements"
    elif score >= 50:
        reasoning = f"Good match with some compromises"
    elif score >= 30:
        reasoning = f"Acceptable but not ideal"
    else:
        reasoning = f"Poor match - may need alternatives"

    return {
        "bed_id": bed.get("bed_id"),
        "bed_number": bed.get("bed_number", bed.get("bed_id")),
        "ward": bed.get("ward"),
        "score": score,
        "reasoning": reasoning,
        "pros": pros,
        "cons": cons,
        "features": bed_features,
    }


def score_cleaner_workload(cleaner: Dict[str, Any], context: str) -> Dict[str, Any]:
    """
    Score cleaner based on workload
    Pure function - deterministic scoring
    """
    current_tasks = cleaner.get("current_tasks", 0)
    cleaner_id = cleaner.get("cleaner_id") or cleaner.get("user_id")
    name = cleaner.get("name", f"Cleaner {cleaner_id}")

    # Calculate score (inverse of workload)
    # 0 tasks = 100 points, each task reduces score by 20
    score = max(0, 100 - (current_tasks * 20))

    # Urgency bonus for post_discharge
    if context == "post_discharge" and current_tasks < 2:
        score += 10

    reasoning_parts = []
    if current_tasks == 0:
        reasoning_parts.append("No current tasks")
    elif current_tasks == 1:
        reasoning_parts.append("Manageable workload (1 task)")
    elif current_tasks == 2:
        reasoning_parts.append("Moderate workload (2 tasks)")
    else:
        reasoning_parts.append(f"Heavy workload ({current_tasks} tasks)")

    if context == "post_discharge":
        reasoning_parts.append("post-discharge cleaning")
    else:
        reasoning_parts.append("pre-admission preparation")

    return {
        "cleaner_id": cleaner_id,
        "name": name,
        "current_tasks": current_tasks,
        "score": score,
        "reasoning": " - ".join(reasoning_parts),
    }


def score_nurse_assignment(
    nurse: Dict[str, Any], patient: Dict[str, Any], bed: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Score nurse based on skills, workload, and ward match
    Pure function - deterministic scoring
    """
    nurse_id = nurse.get("nurse_id") or nurse.get("user_id")
    name = nurse.get("name", f"Nurse {nurse_id}")
    skills = nurse.get("skills", [])
    skills_lower = [s.lower() for s in skills]
    current_patients = nurse.get("current_patients", 0)
    ward = bed.get("ward", "").lower()

    score = 0
    reasoning_parts = []

    # Workload scoring (max 40 points)
    if current_patients == 0:
        score += 40
        reasoning_parts.append("No current patients")
    elif current_patients == 1:
        score += 30
        reasoning_parts.append("Light workload (1 patient)")
    elif current_patients == 2:
        score += 20
        reasoning_parts.append("Moderate workload (2 patients)")
    elif current_patients == 3:
        score += 10
        reasoning_parts.append("Heavy workload (3 patients)")
    else:
        reasoning_parts.append(f"Very heavy workload ({current_patients} patients)")

    # Skills matching (max 40 points)
    diagnosis = patient.get("diagnosis", "").lower()
    special_needs = [s.lower() for s in patient.get("special_needs", [])]

    if "isolation" in ward and "isolation" in skills_lower:
        score += 30
        reasoning_parts.append("Isolation trained")
    elif "icu" in ward and "icu" in skills_lower:
        score += 35
        reasoning_parts.append("ICU trained")
    elif "pediatric" in ward and "pediatric" in skills_lower:
        score += 30
        reasoning_parts.append("Pediatric specialist")
    elif "general" in skills_lower:
        score += 15
        reasoning_parts.append("General care qualified")

    # Ward familiarity (max 20 points)
    assigned_ward = nurse.get("assigned_ward", "").lower()
    if assigned_ward == ward:
        score += 20
        reasoning_parts.append("Familiar with ward")
    elif assigned_ward:
        score += 10
        reasoning_parts.append("Can work in this ward")
    else:
        score += 15
        reasoning_parts.append("Flexible assignment")

    return {
        "nurse_id": nurse_id,
        "name": name,
        "skills": skills,
        "current_patients": current_patients,
        "score": score,
        "reasoning": " | ".join(reasoning_parts),
    }


# ==================== HEALTH CHECK ====================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents_ready": True,
        "timestamp": datetime.now().isoformat(),
        "message": "Pure agent server - no database dependencies",
    }


# ==================== AGENT ENDPOINTS ====================


@app.post("/agent/bed-assignment", response_model=BedAgentResponse)
async def bed_assignment_agent(request: BedAgentRequest):
    """
    Bed Assignment Agent

    Receives: patient info, doctor input, available beds from BACKEND
    Returns: recommended bed_id + reason

    NO DATABASE ACCESS - pure computation only
    """
    try:
        patient = request.patient
        doctor_input = request.doctor_input
        available_beds = request.available_beds

        logger.info(f"Bed assignment request for patient: {patient.get('patient_id')}")

        # Validate input
        if not available_beds:
            return BedAgentResponse(recommended_bed_id=None, reason="No beds available")

        # Extract requirements from diagnosis
        diagnosis = doctor_input.get("diagnosis", "")
        instructions = doctor_input.get("special_instructions", "")
        requirements = extract_requirements_from_diagnosis(diagnosis, instructions)

        # Score all beds
        scored_beds = []
        for bed in available_beds:
            bed_score = score_bed_match(bed, requirements, patient)
            scored_beds.append(bed_score)

        # Sort by score (highest first)
        scored_beds.sort(key=lambda x: x["score"], reverse=True)

        # Get best recommendation
        if scored_beds:
            best_bed = scored_beds[0]

            # Only recommend if score is acceptable (>30)
            if best_bed["score"] >= 30:
                reason = f"{best_bed['reasoning']}. Ward: {best_bed['ward']}. "
                if best_bed["pros"]:
                    reason += f"Pros: {', '.join(best_bed['pros'][:2])}."

                logger.info(
                    f"Recommended bed: {best_bed['bed_id']} (score: {best_bed['score']})"
                )

                return BedAgentResponse(
                    recommended_bed_id=best_bed["bed_id"], reason=reason
                )
            else:
                return BedAgentResponse(
                    recommended_bed_id=None,
                    reason=f"No suitable bed found. Best match scored only {best_bed['score']}/100.",
                )
        else:
            return BedAgentResponse(
                recommended_bed_id=None, reason="No beds available for evaluation"
            )

    except Exception as e:
        logger.error(f"Error in bed assignment: {e}")
        return BedAgentResponse(
            recommended_bed_id=None, reason=f"Error processing request: {str(e)}"
        )


@app.post("/agent/cleaner-assignment", response_model=CleanerAgentResponse)
async def cleaner_assignment_agent(request: CleanerAgentRequest):
    """
    Cleaner Assignment Agent

    Receives: bed_id, context, available cleaners from BACKEND
    Returns: selected cleaner_id + reason

    NO DATABASE ACCESS - pure computation only
    """
    try:
        bed_id = request.bed_id
        context = request.context
        available_cleaners = request.available_cleaners

        logger.info(f"Cleaner assignment for bed {bed_id} ({context})")

        # Validate input
        if not available_cleaners:
            return CleanerAgentResponse(
                selected_cleaner_id=None, reason="No cleaners available"
            )

        # Score all cleaners
        scored_cleaners = []
        for cleaner in available_cleaners:
            cleaner_score = score_cleaner_workload(cleaner, context)
            scored_cleaners.append(cleaner_score)

        # Sort by score (highest first)
        scored_cleaners.sort(key=lambda x: x["score"], reverse=True)

        # Get best cleaner
        best_cleaner = scored_cleaners[0]

        logger.info(
            f"Selected cleaner: {best_cleaner['cleaner_id']} (score: {best_cleaner['score']})"
        )

        return CleanerAgentResponse(
            selected_cleaner_id=best_cleaner["cleaner_id"],
            reason=best_cleaner["reasoning"],
        )

    except Exception as e:
        logger.error(f"Error in cleaner assignment: {e}")
        # Fallback to first cleaner
        if available_cleaners:
            first_cleaner = available_cleaners[0]
            cleaner_id = first_cleaner.get("cleaner_id") or first_cleaner.get("user_id")
            return CleanerAgentResponse(
                selected_cleaner_id=cleaner_id,
                reason=f"Fallback assignment due to error: {str(e)}",
            )
        return CleanerAgentResponse(selected_cleaner_id=None, reason=f"Error: {str(e)}")


@app.post("/agent/nurse-assignment", response_model=NurseAgentResponse)
async def nurse_assignment_agent(request: NurseAgentRequest):
    """
    Nurse Assignment Agent

    Receives: patient, bed, available nurses from BACKEND
    Returns: selected nurse_id + reason

    NO DATABASE ACCESS - pure computation only
    """
    try:
        patient = request.patient
        bed = request.bed
        available_nurses = request.available_nurses

        logger.info(f"Nurse assignment for patient {patient.get('patient_id')}")

        # Validate input
        if not available_nurses:
            return NurseAgentResponse(
                selected_nurse_id=None, reason="No nurses available"
            )

        # Score all nurses
        scored_nurses = []
        for nurse in available_nurses:
            nurse_score = score_nurse_assignment(nurse, patient, bed)
            scored_nurses.append(nurse_score)

        # Sort by score (highest first)
        scored_nurses.sort(key=lambda x: x["score"], reverse=True)

        # Get best nurse
        best_nurse = scored_nurses[0]

        logger.info(
            f"Selected nurse: {best_nurse['nurse_id']} (score: {best_nurse['score']})"
        )

        return NurseAgentResponse(
            selected_nurse_id=best_nurse["nurse_id"], reason=best_nurse["reasoning"]
        )

    except Exception as e:
        logger.error(f"Error in nurse assignment: {e}")
        # Fallback to first nurse
        if available_nurses:
            first_nurse = available_nurses[0]
            nurse_id = first_nurse.get("nurse_id") or first_nurse.get("user_id")
            return NurseAgentResponse(
                selected_nurse_id=nurse_id,
                reason=f"Fallback assignment due to error: {str(e)}",
            )
        return NurseAgentResponse(selected_nurse_id=None, reason=f"Error: {str(e)}")


# ==================== MAIN ====================


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AGENT_SERVER_PORT", "9000"))

    logger.info("=" * 60)
    logger.info("CareFlow Pure Agent Server Starting...")
    logger.info("NO DATABASE ACCESS - Pure computation only")
    logger.info(f"Port: {port}")
    logger.info("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=port)
