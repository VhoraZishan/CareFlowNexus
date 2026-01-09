"""
Bed Allocator Agent for CareFlow Nexus
Agent 2: Matches patient diagnosis to best available beds

This agent is 50% rule-based (scoring algorithm) and 50% AI (ranking and reasoning)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from base_agent import BaseAgent
from prompts.prompt_templates import BedAllocatorPrompts
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService
from utils.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class BedAllocatorAgent(BaseAgent):
    """
    Bed Allocator Agent - Matches patients to optimal beds

    Responsibilities:
    - Extract patient requirements from diagnosis
    - Score beds using rule-based algorithm (50%)
    - Enhance with AI ranking and reasoning (50%)
    - Generate top 3 bed recommendations
    - Learn from human overrides
    """

    def __init__(
        self,
        firebase_service: FirebaseService,
        gemini_service: GeminiService,
        memory_agent,
        rule_weight: float = 0.5,
    ):
        """
        Initialize Bed Allocator Agent

        Args:
            firebase_service: Firebase service instance
            gemini_service: Gemini AI service instance
            memory_agent: Memory agent for state queries
            rule_weight: Weight for rule-based score (0.5 = 50/50)
        """
        super().__init__(
            agent_id="bed_allocator_001",
            agent_type="bed_allocator",
            firebase_service=firebase_service,
            gemini_service=gemini_service,
        )

        self.memory_agent = memory_agent
        self.rule_weight = rule_weight
        self.ai_weight = 1.0 - rule_weight
        self.allocation_history = []

        self.logger.info(
            f"Bed Allocator Agent initialized (Rule: {rule_weight * 100}%, AI: {self.ai_weight * 100}%)"
        )

    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bed allocation request

        Args:
            request_data: Request with 'patient_id'

        Returns:
            Response with bed recommendations
        """
        try:
            # Validate input
            is_valid, missing = self.validate_input(request_data, ["patient_id"])
            if not is_valid:
                return self.format_response(
                    False,
                    None,
                    f"Missing required fields: {missing}",
                    "invalid_input",
                )

            patient_id = request_data["patient_id"]

            # Get patient data
            patient = await self.firebase.get_patient(patient_id)
            if not patient:
                return self.format_response(
                    False, None, f"Patient {patient_id} not found", "patient_not_found"
                )

            # Step 1: Extract requirements (AI-powered)
            self.logger.info(
                f"Extracting requirements for patient: {patient.get('name')}"
            )
            requirements = await self.extract_requirements(patient)

            # Step 2: Get available beds from memory agent
            self.logger.info("Fetching available beds from memory agent")
            available_beds_response = await self.memory_agent.process(
                {"type": "get_available_beds"}
            )
            available_beds = available_beds_response.get("data", [])

            if not available_beds:
                return self.format_response(
                    False,
                    {"requirements": requirements},
                    "No beds available",
                    "no_beds",
                )

            # Step 3: Filter beds by hard requirements (rule-based)
            self.logger.info("Filtering beds by requirements")
            suitable_beds = self._filter_beds_by_requirements(
                available_beds, requirements
            )

            if not suitable_beds:
                return self.format_response(
                    False,
                    {"requirements": requirements},
                    "No beds match patient requirements",
                    "no_suitable_beds",
                )

            # Step 4: Score beds using rule-based algorithm
            self.logger.info(f"Scoring {len(suitable_beds)} suitable beds")
            scored_beds = await self._score_beds_rule_based(
                suitable_beds, patient, requirements
            )

            # Step 5: Get AI rankings and reasoning
            self.logger.info("Getting AI-enhanced rankings")
            ai_recommendations = await self._get_ai_recommendations(
                patient,
                requirements,
                scored_beds[:10],  # Top 10 for AI
            )

            # Step 6: Combine rule-based and AI scores
            self.logger.info("Combining rule-based and AI scores")
            final_recommendations = self._combine_scores(
                scored_beds, ai_recommendations
            )

            # Prepare response
            result = {
                "patient_id": patient_id,
                "patient_name": patient.get("name"),
                "diagnosis": patient.get("diagnosis"),
                "severity": patient.get("severity"),
                "requirements": requirements,
                "recommendations": final_recommendations["top_3"],
                "confidence": final_recommendations["confidence"],
                "scoring_method": f"Hybrid (Rule: {self.rule_weight * 100}%, AI: {self.ai_weight * 100}%)",
            }

            # Log decision
            await self.log_decision(
                action="bed_allocation",
                input_data={"patient_id": patient_id, "requirements": requirements},
                output_data=result,
                reasoning=f"Generated {len(final_recommendations['top_3'])} recommendations",
            )

            return self.format_response(True, result, "Bed allocation successful")

        except Exception as e:
            self.logger.error(f"Error in bed allocation: {e}")
            await self.log_error(str(e), request_data, "allocation_error")
            return self.format_response(False, None, str(e), "processing_error")

    # ==================== REQUIREMENT EXTRACTION (AI) ====================

    async def extract_requirements(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract patient requirements using AI + rules

        Args:
            patient: Patient data dictionary

        Returns:
            Requirements dictionary
        """
        try:
            # If requirements already exist, use them
            if "requirements" in patient and patient["requirements"]:
                existing_req = patient["requirements"]
                self.logger.info("Using existing patient requirements")

                # Enhance with AI if diagnosis is present
                if "diagnosis" in patient and patient["diagnosis"]:
                    ai_req = await self._extract_requirements_ai(patient)
                    # Merge AI requirements with existing ones
                    existing_req.update(
                        {
                            k: v
                            for k, v in ai_req.items()
                            if k
                            not in ["confidence", "reasoning", "special_considerations"]
                        }
                    )
                    return existing_req

                return existing_req

            # Extract using AI
            if "diagnosis" in patient and patient["diagnosis"]:
                return await self._extract_requirements_ai(patient)

            # Fallback: basic requirements
            return self._extract_requirements_basic(patient)

        except Exception as e:
            self.logger.error(f"Error extracting requirements: {e}")
            return self._extract_requirements_basic(patient)

    async def _extract_requirements_ai(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Use Gemini AI to extract requirements from diagnosis"""
        try:
            prompt = BedAllocatorPrompts.REQUIREMENT_EXTRACTION.format(
                age=patient.get("age", "Unknown"),
                gender=patient.get("gender", "Unknown"),
                diagnosis=patient.get("diagnosis", "No diagnosis"),
                severity=patient.get("severity", "moderate"),
                admission_type=patient.get("admission_type", "emergency"),
                mobility_status=patient.get("mobility_status", "ambulatory"),
            )

            response = await self.gemini.generate_json_response(prompt, temperature=0.3)

            if response:
                parsed = ResponseParser.parse_requirement_extraction_response(response)
                self.logger.info(
                    f"AI extracted requirements with {parsed['confidence']}% confidence"
                )
                return parsed

            return self._extract_requirements_basic(patient)

        except Exception as e:
            self.logger.error(f"Error in AI requirement extraction: {e}")
            return self._extract_requirements_basic(patient)

    def _extract_requirements_basic(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Basic rule-based requirement extraction"""
        diagnosis = patient.get("diagnosis", "").lower()
        severity = patient.get("severity", "moderate").lower()

        requirements = {
            "needs_oxygen": False,
            "needs_ventilator": False,
            "needs_cardiac_monitor": False,
            "needs_isolation": False,
            "preferred_ward": None,
            "proximity_preference": 5,
            "special_considerations": [],
        }

        # Basic pattern matching
        if any(
            term in diagnosis
            for term in ["respiratory", "pneumonia", "copd", "asthma", "lung"]
        ):
            requirements["needs_oxygen"] = True
            requirements["preferred_ward"] = "Respiratory"

        if any(term in diagnosis for term in ["cardiac", "heart", "mi", "arrhythmia"]):
            requirements["needs_cardiac_monitor"] = True
            requirements["preferred_ward"] = "Cardiac"

        if any(
            term in diagnosis for term in ["infectious", "covid", "tb", "contagious"]
        ):
            requirements["needs_isolation"] = True

        if severity == "critical":
            requirements["proximity_preference"] = 9
            requirements["needs_cardiac_monitor"] = True
        elif severity == "high":
            requirements["proximity_preference"] = 7

        return requirements

    # ==================== BED FILTERING (RULE-BASED) ====================

    def _filter_beds_by_requirements(
        self, beds: List[Dict], requirements: Dict
    ) -> List[Dict]:
        """
        Filter beds by hard requirements

        Args:
            beds: List of available beds
            requirements: Patient requirements

        Returns:
            List of suitable beds
        """
        suitable = []

        for bed in beds:
            equipment = bed.get("equipment", {})

            # Check oxygen requirement
            if requirements.get("needs_oxygen") and not equipment.get("has_oxygen"):
                continue

            # Check ventilator requirement
            if requirements.get("needs_ventilator") and not equipment.get(
                "has_ventilator"
            ):
                continue

            # Check cardiac monitor requirement
            if requirements.get("needs_cardiac_monitor") and not equipment.get(
                "has_cardiac_monitor"
            ):
                continue

            # Check isolation requirement
            if requirements.get("needs_isolation") and not equipment.get(
                "is_isolation"
            ):
                continue

            suitable.append(bed)

        self.logger.info(
            f"Filtered {len(suitable)} beds from {len(beds)} available beds"
        )
        return suitable

    # ==================== RULE-BASED SCORING (50%) ====================

    async def _score_beds_rule_based(
        self, beds: List[Dict], patient: Dict, requirements: Dict
    ) -> List[Dict]:
        """
        Score beds using rule-based algorithm

        Scoring breakdown:
        - Equipment match: 40 points
        - Ward appropriateness: 25 points
        - Proximity to nursing: 15 points
        - Availability: 10 points
        - Workload distribution: 10 points

        Args:
            beds: List of suitable beds
            patient: Patient data
            requirements: Patient requirements

        Returns:
            List of beds with rule_based_score
        """
        scored_beds = []

        for bed in beds:
            score = 0
            reasoning_parts = []
            equipment = bed.get("equipment", {})

            # 1. Equipment Match (40 points max)
            equipment_score = 0
            if requirements.get("needs_oxygen") and equipment.get("has_oxygen"):
                equipment_score += 15
                reasoning_parts.append("Has required oxygen supply")
            elif equipment.get("has_oxygen"):
                equipment_score += 5  # Bonus for having it even if not required

            if requirements.get("needs_ventilator") and equipment.get("has_ventilator"):
                equipment_score += 15
                reasoning_parts.append("Has required ventilator")
            elif equipment.get("has_ventilator"):
                equipment_score += 5

            if requirements.get("needs_cardiac_monitor") and equipment.get(
                "has_cardiac_monitor"
            ):
                equipment_score += 10
                reasoning_parts.append("Has cardiac monitoring")
            elif equipment.get("has_cardiac_monitor"):
                equipment_score += 3

            score += min(equipment_score, 40)

            # 2. Ward Appropriateness (25 points max)
            preferred_ward = requirements.get("preferred_ward")
            bed_ward = bed.get("ward", "")

            if preferred_ward and bed_ward == preferred_ward:
                score += 25
                reasoning_parts.append(f"Located in preferred {bed_ward} ward")
            elif preferred_ward and preferred_ward.lower() in bed_ward.lower():
                score += 15  # Partial match
                reasoning_parts.append(f"Located in related {bed_ward} ward")
            else:
                score += 10  # Any ward gets some points

            # 3. Proximity to Nursing Station (15 points max)
            proximity = bed.get("proximity_to_nursing_station", 5)
            preferred_proximity = requirements.get("proximity_preference", 5)

            # Score based on how close to preferred proximity
            proximity_diff = abs(proximity - preferred_proximity)
            proximity_score = max(0, 15 - (proximity_diff * 2))
            score += proximity_score

            if proximity >= 7:
                reasoning_parts.append("Close to nursing station for monitoring")

            # 4. Availability Score (10 points)
            if bed.get("status") == "ready":
                score += 10
                reasoning_parts.append("Currently available and ready")

            # 5. Workload Distribution (10 points)
            # TODO: Could check ward occupancy here
            score += 10

            # Store scored bed
            scored_beds.append(
                {
                    **bed,
                    "rule_based_score": score,
                    "reasoning_parts": reasoning_parts,
                }
            )

        # Sort by score (highest first)
        scored_beds.sort(key=lambda x: x["rule_based_score"], reverse=True)

        self.logger.info(
            f"Rule-based scoring complete. Top score: {scored_beds[0]['rule_based_score'] if scored_beds else 0}"
        )
        return scored_beds

    # ==================== AI RANKING (50%) ====================

    async def _get_ai_recommendations(
        self, patient: Dict, requirements: Dict, beds: List[Dict]
    ) -> Dict[str, Any]:
        """
        Get AI-enhanced recommendations from Gemini

        Args:
            patient: Patient data
            requirements: Extracted requirements
            beds: Top beds from rule-based scoring

        Returns:
            AI recommendations dictionary
        """
        try:
            # Prepare beds data for AI (simplified)
            beds_for_ai = []
            for bed in beds:
                beds_for_ai.append(
                    {
                        "bed_id": bed.get("id"),
                        "bed_number": bed.get("bed_number"),
                        "ward": bed.get("ward"),
                        "equipment": bed.get("equipment"),
                        "proximity": bed.get("proximity_to_nursing_station"),
                        "rule_score": bed.get("rule_based_score"),
                    }
                )

            # Get current context
            state_response = await self.memory_agent.process(
                {"type": "get_system_state"}
            )
            state = state_response.get("data", {})

            # Build prompt
            prompt = BedAllocatorPrompts.BED_ALLOCATION.format(
                patient_name=patient.get("name", "Unknown"),
                age=patient.get("age", "Unknown"),
                gender=patient.get("gender", "Unknown"),
                diagnosis=patient.get("diagnosis", "No diagnosis"),
                severity=patient.get("severity", "moderate"),
                mobility_status=patient.get("mobility_status", "ambulatory"),
                needs_oxygen=requirements.get("needs_oxygen", False),
                needs_ventilator=requirements.get("needs_ventilator", False),
                needs_cardiac_monitor=requirements.get("needs_cardiac_monitor", False),
                needs_isolation=requirements.get("needs_isolation", False),
                preferred_ward=requirements.get("preferred_ward", "Any"),
                beds_json=self._format_beds_for_prompt(beds_for_ai),
                current_time=datetime.now().strftime("%H:%M"),
                day_of_week=datetime.now().strftime("%A"),
                occupancy_rate=state.get("beds", {}).get("total", 0),
                staff_summary=f"Nurses: {state.get('staff', {}).get('nurses', 0)}, Cleaners: {state.get('staff', {}).get('cleaners', 0)}",
            )

            # Call Gemini AI
            response = await self.gemini.generate_json_response(prompt, temperature=0.5)

            if response:
                parsed = ResponseParser.parse_bed_allocation_response(response)
                self.logger.info(
                    f"AI generated {len(parsed['recommendations'])} recommendations with {parsed['overall_confidence']}% confidence"
                )
                return parsed

            return {
                "recommendations": [],
                "overall_confidence": 0,
                "considerations": "",
            }

        except Exception as e:
            self.logger.error(f"Error getting AI recommendations: {e}")
            return {
                "recommendations": [],
                "overall_confidence": 0,
                "considerations": "",
            }

    def _format_beds_for_prompt(self, beds: List[Dict]) -> str:
        """Format beds for AI prompt"""
        lines = []
        for i, bed in enumerate(beds, 1):
            equipment = bed.get("equipment", {})
            equip_list = []
            if equipment.get("has_oxygen"):
                equip_list.append("Oxygen")
            if equipment.get("has_ventilator"):
                equip_list.append("Ventilator")
            if equipment.get("has_cardiac_monitor"):
                equip_list.append("Cardiac Monitor")
            if equipment.get("is_isolation"):
                equip_list.append("Isolation")

            lines.append(
                f"{i}. Bed {bed.get('bed_number')} ({bed.get('ward')})\n"
                f"   Equipment: {', '.join(equip_list) if equip_list else 'Standard'}\n"
                f"   Proximity: {bed.get('proximity')}/10\n"
                f"   Rule Score: {bed.get('rule_score')}/100"
            )

        return "\n\n".join(lines)

    # ==================== SCORE COMBINATION (HYBRID) ====================

    def _combine_scores(
        self, rule_based_beds: List[Dict], ai_recommendations: Dict
    ) -> Dict[str, Any]:
        """
        Combine rule-based and AI scores

        Args:
            rule_based_beds: Beds with rule-based scores
            ai_recommendations: AI recommendations

        Returns:
            Combined recommendations with top 3
        """
        # Create mapping of bed_id to AI recommendation
        ai_map = {}
        for rec in ai_recommendations.get("recommendations", []):
            bed_id = rec.get("bed_id")
            if bed_id:
                ai_map[bed_id] = rec

        combined = []
        for bed in rule_based_beds:
            bed_id = bed.get("id")
            rule_score = bed.get("rule_based_score", 0)

            # Get AI score if available
            ai_rec = ai_map.get(bed_id)
            ai_score = ai_rec.get("score", rule_score) if ai_rec else rule_score

            # Combine scores: 50% rule-based, 50% AI
            final_score = ResponseParser.combine_scores(
                rule_score, ai_score, self.rule_weight
            )

            # Prepare recommendation
            combined.append(
                {
                    "bed_id": bed_id,
                    "bed_number": bed.get("bed_number"),
                    "ward": bed.get("ward"),
                    "floor": bed.get("floor"),
                    "equipment": bed.get("equipment"),
                    "proximity_to_nursing_station": bed.get(
                        "proximity_to_nursing_station"
                    ),
                    "score": final_score,
                    "rule_score": rule_score,
                    "ai_score": ai_score,
                    "reasoning": ai_rec.get("reasoning")
                    if ai_rec
                    else " ".join(bed.get("reasoning_parts", [])),
                    "pros": ai_rec.get("pros", bed.get("reasoning_parts", []))
                    if ai_rec
                    else bed.get("reasoning_parts", []),
                    "cons": ai_rec.get("cons", []) if ai_rec else [],
                }
            )

        # Sort by final score
        combined.sort(key=lambda x: x["score"], reverse=True)

        # Get top 3
        top_3 = combined[:3]

        # Calculate average confidence
        confidence = ai_recommendations.get("overall_confidence", 75)
        if not ai_recommendations.get("recommendations"):
            # If no AI recommendations, lower confidence slightly
            confidence = 70

        return {
            "top_3": top_3,
            "all_options": combined,
            "confidence": confidence,
            "considerations": ai_recommendations.get("considerations", ""),
        }

    # ==================== LEARNING & FEEDBACK ====================

    async def record_allocation_feedback(
        self,
        allocation_id: str,
        patient_id: str,
        recommended_beds: List[str],
        chosen_bed_id: str,
        was_override: bool,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Record allocation feedback for learning

        Args:
            allocation_id: Unique allocation ID
            patient_id: Patient ID
            recommended_beds: List of recommended bed IDs
            chosen_bed_id: Bed that was actually chosen
            was_override: True if human overrode AI recommendation
            reason: Optional reason for override

        Returns:
            True if recorded successfully
        """
        try:
            feedback = {
                "allocation_id": allocation_id,
                "patient_id": patient_id,
                "recommended_beds": recommended_beds,
                "chosen_bed_id": chosen_bed_id,
                "was_override": was_override,
                "override_reason": reason,
                "timestamp": datetime.now().isoformat(),
            }

            await self.firebase.log_event(
                {
                    "entity_type": "allocation_feedback",
                    "entity_id": allocation_id,
                    "action": "override" if was_override else "confirmed",
                    "triggered_by": self.agent_type,
                    "details": feedback,
                }
            )

            self.allocation_history.append(feedback)
            self.logger.info(
                f"Recorded allocation feedback: {'Override' if was_override else 'Confirmed'}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error recording feedback: {e}")
            return False

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "extract_requirements",
            "allocate_bed",
            "score_beds",
            "rank_beds",
            "record_feedback",
        ]
