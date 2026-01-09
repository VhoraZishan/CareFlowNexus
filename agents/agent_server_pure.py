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
    Score cleaner based on workload, experience, specialties, and skills
    Uses detailed profiles created in database initialization
    Pure function - deterministic scoring
    """
    current_tasks = cleaner.get("current_tasks", 0)
    cleaner_id = cleaner.get("cleaner_id") or cleaner.get("user_id")
    name = cleaner.get("name", f"Cleaner {cleaner_id}")

    # Get detailed profile data
    experience_years = cleaner.get("experience_years", 0)
    specialties = cleaner.get("specialties", [])
    certifications = cleaner.get("certifications", [])
    skills = cleaner.get("skills", {})
    clearance_level = cleaner.get("clearance_level", "standard")
    department_expertise = cleaner.get("department_expertise", [])
    average_room_time = cleaner.get("average_room_time", 45)
    max_tasks_per_shift = cleaner.get("max_tasks_per_shift", 10)

    score = 0
    reasoning_parts = []

    # 1. Workload scoring (max 30 points)
    workload_capacity = max_tasks_per_shift - current_tasks
    if workload_capacity <= 0:
        score += 0
        reasoning_parts.append(
            f"At capacity ({current_tasks}/{max_tasks_per_shift} tasks)"
        )
    elif current_tasks == 0:
        score += 30
        reasoning_parts.append("Available - no current tasks")
    elif current_tasks <= max_tasks_per_shift * 0.3:
        score += 25
        reasoning_parts.append(f"Light load ({current_tasks}/{max_tasks_per_shift})")
    elif current_tasks <= max_tasks_per_shift * 0.6:
        score += 15
        reasoning_parts.append(f"Moderate load ({current_tasks}/{max_tasks_per_shift})")
    else:
        score += 5
        reasoning_parts.append(f"Heavy load ({current_tasks}/{max_tasks_per_shift})")

    # 2. Experience scoring (max 25 points)
    if experience_years >= 20:
        score += 25
        reasoning_parts.append(f"Veteran ({experience_years}yr)")
    elif experience_years >= 10:
        score += 20
        reasoning_parts.append(f"Experienced ({experience_years}yr)")
    elif experience_years >= 5:
        score += 15
        reasoning_parts.append(f"Skilled ({experience_years}yr)")
    else:
        score += 10
        reasoning_parts.append(f"Junior ({experience_years}yr)")

    # 3. Specialty matching (max 30 points)
    specialties_lower = [s.lower() for s in specialties]
    department_expertise_lower = [d.lower() for d in department_expertise]

    specialty_matched = False

    if context == "pre_admission":
        # For pre-admission, look for preparation and sterilization skills
        if any("icu" in s for s in specialties_lower):
            score += 30
            reasoning_parts.append("ICU specialist")
            specialty_matched = True
        elif any(
            "surgery" in s or "or" in s or "sterile" in s for s in specialties_lower
        ):
            score += 28
            reasoning_parts.append("Surgery/OR specialist")
            specialty_matched = True
        elif any("er" in s or "emergency" in s for s in specialties_lower):
            score += 25
            reasoning_parts.append("ER specialist")
            specialty_matched = True
    else:  # post_discharge
        # For post-discharge, prioritize thorough cleaning and infection control
        if any("isolation" in s or "infectious" in s for s in specialties_lower):
            score += 30
            reasoning_parts.append("Isolation/Infection control expert")
            specialty_matched = True
        elif any("icu" in s for s in specialties_lower):
            score += 28
            reasoning_parts.append("ICU deep cleaning specialist")
            specialty_matched = True
        elif any("hazmat" in s or "biohazard" in s for s in specialties_lower):
            score += 26
            reasoning_parts.append("Hazmat/Biohazard certified")
            specialty_matched = True

    if not specialty_matched:
        if any("general" in s for s in specialties_lower):
            score += 18
            reasoning_parts.append("General cleaning qualified")
        else:
            score += 10

    # 4. Skill ratings (max 15 points) - check relevant skills
    relevant_skill_score = 0
    skills_mentioned = []

    if context == "pre_admission":
        if skills.get("sterile_technique", 0) >= 90:
            relevant_skill_score += 5
            skills_mentioned.append("sterile technique")
        if skills.get("equipment_sterilization", 0) >= 85:
            relevant_skill_score += 5
            skills_mentioned.append("equipment sterilization")
    else:  # post_discharge
        if skills.get("infection_control", 0) >= 90:
            relevant_skill_score += 5
            skills_mentioned.append("infection control")
        if skills.get("terminal_cleaning", 0) >= 85:
            relevant_skill_score += 5
            skills_mentioned.append("terminal cleaning")

    # Check general high-level skills
    if skills.get("icu_cleaning", 0) >= 90 or skills.get("or_cleaning", 0) >= 90:
        relevant_skill_score += 5
        skills_mentioned.append("expert-level cleaning")

    score += relevant_skill_score
    if skills_mentioned:
        reasoning_parts.append(f"Skills: {', '.join(skills_mentioned[:2])}")

    # 5. Clearance level bonus
    if clearance_level == "high_risk":
        score += 10
        reasoning_parts.append("High-risk clearance")

    # 6. Efficiency bonus based on room time
    if average_room_time <= 30:
        score += 5
        reasoning_parts.append("Fast turnover")
    elif average_room_time >= 55:
        score -= 3
        reasoning_parts.append("Thorough but slower")

    # Context-specific adjustments
    if context == "post_discharge" and current_tasks < 2:
        score += 5  # Bonus for availability during discharge

    return {
        "cleaner_id": cleaner_id,
        "name": name,
        "current_tasks": current_tasks,
        "experience_years": experience_years,
        "specialties": specialties,
        "clearance_level": clearance_level,
        "score": score,
        "reasoning": " | ".join(reasoning_parts),
    }


def score_nurse_assignment(
    nurse: Dict[str, Any], patient: Dict[str, Any], bed: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Score nurse based on experience, specialties, skills, certifications, and workload
    Uses detailed profiles created in database initialization
    Pure function - deterministic scoring
    """
    nurse_id = nurse.get("nurse_id") or nurse.get("user_id")
    name = nurse.get("name", f"Nurse {nurse_id}")

    # Get detailed profile data
    experience_years = nurse.get("experience_years", 0)
    specialties = nurse.get("specialties", [])
    certifications = nurse.get("certifications", [])
    skills = nurse.get("skills", {})
    department = nurse.get("department", "")
    languages = nurse.get("languages", [])
    max_patients = nurse.get("max_patients", 5)
    current_patients = nurse.get("current_patients", 0)

    # Patient and bed info
    ward = bed.get("ward", "").lower()
    bed_type = bed.get("type", "").lower()
    diagnosis = patient.get("admission", {}).get("diagnosis", "").lower()
    special_needs = patient.get("special_needs", [])
    patient_age = patient.get("age", 0)

    score = 0
    reasoning_parts = []

    # 1. Workload scoring (max 25 points)
    workload_capacity = max_patients - current_patients
    if workload_capacity <= 0:
        score += 0
        reasoning_parts.append(f"At capacity ({current_patients}/{max_patients})")
    elif current_patients == 0:
        score += 25
        reasoning_parts.append("Available - no patients")
    elif current_patients <= max_patients * 0.4:
        score += 20
        reasoning_parts.append(f"Light load ({current_patients}/{max_patients})")
    elif current_patients <= max_patients * 0.7:
        score += 12
        reasoning_parts.append(f"Moderate load ({current_patients}/{max_patients})")
    else:
        score += 5
        reasoning_parts.append(f"Heavy load ({current_patients}/{max_patients})")

    # 2. Experience scoring (max 20 points)
    if experience_years >= 20:
        score += 20
        reasoning_parts.append(f"Veteran ({experience_years}yr)")
    elif experience_years >= 15:
        score += 18
        reasoning_parts.append(f"Very experienced ({experience_years}yr)")
    elif experience_years >= 10:
        score += 15
        reasoning_parts.append(f"Experienced ({experience_years}yr)")
    elif experience_years >= 5:
        score += 12
        reasoning_parts.append(f"Skilled ({experience_years}yr)")
    else:
        score += 8
        reasoning_parts.append(f"Junior ({experience_years}yr)")

    # 3. Specialty and Department matching (max 35 points)
    specialties_lower = [s.lower() for s in specialties]
    department_lower = department.lower()

    specialty_matched = False

    # Check for critical care needs
    if "cardiac" in diagnosis or "heart" in diagnosis or "myocardial" in diagnosis:
        if "cardiology" in specialties_lower or "cardiac" in department_lower:
            score += 35
            reasoning_parts.append("Cardiac specialist")
            specialty_matched = True
        elif "critical care" in specialties_lower or "icu" in specialties_lower:
            score += 28
            reasoning_parts.append("Critical care trained")
            specialty_matched = True

    if "icu" in ward or "icu" in bed_type:
        if "icu" in specialties_lower or "critical care" in specialties_lower:
            score += 35
            reasoning_parts.append("ICU specialist")
            specialty_matched = True

    if "emergency" in diagnosis or "er" in ward:
        if "emergency" in specialties_lower or "trauma" in specialties_lower:
            score += 33
            reasoning_parts.append("Emergency/Trauma expert")
            specialty_matched = True

    if patient_age < 18:
        if "pediatric" in specialties_lower or "pediatrics" in department_lower:
            score += 35
            reasoning_parts.append("Pediatric specialist")
            specialty_matched = True

    if "surgery" in diagnosis or "post-surgical" in diagnosis:
        if "post-surgical" in specialties_lower or "surgery" in department_lower:
            score += 32
            reasoning_parts.append("Post-surgical care expert")
            specialty_matched = True

    if "oncology" in diagnosis or "cancer" in diagnosis or "chemotherapy" in diagnosis:
        if "oncology" in specialties_lower:
            score += 35
            reasoning_parts.append("Oncology specialist")
            specialty_matched = True

    # General department match
    if not specialty_matched:
        if department_lower and (department_lower in ward or ward in department_lower):
            score += 20
            reasoning_parts.append(f"{department} trained")
        elif "general" in specialties_lower:
            score += 12
            reasoning_parts.append("General care qualified")
        else:
            score += 8

    # 4. Skill ratings (max 20 points) - check relevant skills
    relevant_skill_score = 0
    skills_mentioned = []

    # Critical care skills
    if "icu" in ward or "critical" in diagnosis:
        if skills.get("critical_care", 0) >= 90:
            relevant_skill_score += 7
            skills_mentioned.append("expert critical care")
        elif skills.get("critical_care", 0) >= 80:
            relevant_skill_score += 5

    # Emergency response
    if "emergency" in diagnosis or "trauma" in diagnosis:
        if skills.get("emergency_response", 0) >= 90:
            relevant_skill_score += 7
            skills_mentioned.append("expert emergency response")
        elif skills.get("emergency_response", 0) >= 80:
            relevant_skill_score += 5

    # Patient monitoring
    if skills.get("patient_monitoring", 0) >= 90:
        relevant_skill_score += 4
        skills_mentioned.append("expert monitoring")

    # Medication administration (always important)
    if skills.get("medication_administration", 0) >= 90:
        relevant_skill_score += 4

    # Specialty-specific skills
    if "cardiac" in diagnosis and skills.get("cardiac_care", 0) >= 85:
        relevant_skill_score += 6
        skills_mentioned.append("cardiac care")

    if patient_age < 18 and skills.get("pediatric_care", 0) >= 85:
        relevant_skill_score += 6
        skills_mentioned.append("pediatric care")

    score += min(relevant_skill_score, 20)  # Cap at 20 points
    if skills_mentioned:
        reasoning_parts.append(f"Skills: {', '.join(skills_mentioned[:2])}")

    # 5. Certifications bonus (max 10 points)
    cert_score = 0
    if "CCRN" in certifications or "Critical Care Certified" in certifications:
        cert_score += 5
    if "ACLS" in certifications:
        cert_score += 3
    if "PALS" in certifications and patient_age < 18:
        cert_score += 4
    if len(certifications) >= 4:
        cert_score += 2

    score += min(cert_score, 10)
    if cert_score > 0:
        reasoning_parts.append(f"{len(certifications)} certifications")

    # 6. Language matching
    if special_needs:
        for need in special_needs:
            if any(lang.lower() in need.lower() for lang in languages):
                score += 5
                reasoning_parts.append(f"Language match")
                break

    return {
        "nurse_id": nurse_id,
        "name": name,
        "experience_years": experience_years,
        "specialties": specialties,
        "department": department,
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
