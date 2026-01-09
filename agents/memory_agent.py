"""
Memory Agent (State Manager Agent) for CareFlow Nexus
Agent 1: Memorizes all hospital data and provides state queries

This agent is 50% rule-based (data queries, metrics) and 50% AI (analysis, bottleneck detection)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from base_agent import BaseAgent
from prompts.prompt_templates import StateManagerPrompts
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService
from utils.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """
    State Manager Agent - Memorizes and manages hospital state

    Responsibilities:
    - Load and cache all hospital data (beds, staff, patients, tasks)
    - Provide fast queries to other agents
    - Monitor system state in real-time
    - Detect bottlenecks and anomalies (AI-powered)
    - Generate state analysis reports (AI-powered)
    """

    def __init__(
        self,
        firebase_service: FirebaseService,
        gemini_service: GeminiService,
        refresh_interval: int = 300,  # 5 minutes
    ):
        """
        Initialize Memory Agent

        Args:
            firebase_service: Firebase service instance
            gemini_service: Gemini AI service instance
            refresh_interval: How often to refresh state cache (seconds)
        """
        super().__init__(
            agent_id="memory_agent_001",
            agent_type="state_manager",
            firebase_service=firebase_service,
            gemini_service=gemini_service,
        )

        self.refresh_interval = refresh_interval
        self.state_cache = {
            "beds": [],
            "patients": [],
            "staff": [],
            "tasks": [],
            "last_refresh": None,
        }

        self.logger.info("Memory Agent initialized")

    async def initialize(self) -> bool:
        """
        Initialize agent by loading all hospital data

        Returns:
            True if successful
        """
        try:
            self.logger.info("Initializing Memory Agent - loading hospital data...")
            await self.refresh_state()
            self.logger.info("Memory Agent initialization complete")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Memory Agent: {e}")
            return False

    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming requests

        Args:
            request_data: Request with 'type' and optional parameters

        Returns:
            Response dictionary
        """
        try:
            request_type = request_data.get("type", "")

            # Auto-refresh if cache is stale
            await self._check_and_refresh()

            # Route request to appropriate handler
            if request_type == "get_available_beds":
                result = await self.get_available_beds(request_data.get("filters"))
                return self.format_response(True, result, "Available beds retrieved")

            elif request_type == "get_patient_requirements":
                patient_id = request_data.get("patient_id")
                result = await self.get_patient_requirements(patient_id)
                return self.format_response(
                    True, result, "Patient requirements retrieved"
                )

            elif request_type == "get_staff_availability":
                role = request_data.get("role")
                ward = request_data.get("ward")
                result = await self.get_staff_availability(role, ward)
                return self.format_response(
                    True, result, "Staff availability retrieved"
                )

            elif request_type == "get_system_state":
                result = await self.get_system_state()
                return self.format_response(True, result, "System state retrieved")

            elif request_type == "analyze_state":
                result = await self.analyze_state_with_ai()
                return self.format_response(True, result, "State analysis complete")

            elif request_type == "detect_bottlenecks":
                result = await self.detect_bottlenecks()
                return self.format_response(
                    True, result, "Bottleneck detection complete"
                )

            elif request_type == "get_metrics":
                result = await self.get_metrics()
                return self.format_response(True, result, "Metrics retrieved")

            else:
                return self.format_response(
                    False,
                    None,
                    f"Unknown request type: {request_type}",
                    "invalid_request",
                )

        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            await self.log_error(str(e), request_data, "process_error")
            return self.format_response(False, None, str(e), "processing_error")

    # ==================== RULE-BASED METHODS (50%) ====================

    async def refresh_state(self) -> None:
        """Refresh entire hospital state from Firebase"""
        try:
            self.logger.info("Refreshing hospital state cache...")

            # Load all data in parallel would be ideal, but we'll do sequential for simplicity
            self.state_cache["beds"] = await self.firebase.get_all_beds()
            self.state_cache["patients"] = await self.firebase.get_all_patients()
            self.state_cache["staff"] = await self.firebase.get_all_staff()
            self.state_cache["tasks"] = await self.firebase.get_tasks(
                {"status": ["pending", "in_progress"]}
            )
            self.state_cache["last_refresh"] = datetime.now()

            self.logger.info(
                f"State refreshed - Beds: {len(self.state_cache['beds'])}, "
                f"Patients: {len(self.state_cache['patients'])}, "
                f"Staff: {len(self.state_cache['staff'])}, "
                f"Tasks: {len(self.state_cache['tasks'])}"
            )

        except Exception as e:
            self.logger.error(f"Error refreshing state: {e}")
            raise

    async def _check_and_refresh(self) -> None:
        """Check if cache is stale and refresh if needed"""
        last_refresh = self.state_cache.get("last_refresh")

        if last_refresh is None:
            await self.refresh_state()
            return

        time_since_refresh = (datetime.now() - last_refresh).total_seconds()

        if time_since_refresh > self.refresh_interval:
            self.logger.info("Cache is stale, refreshing...")
            await self.refresh_state()

    async def get_available_beds(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get available beds with optional filters (RULE-BASED)

        Args:
            filters: Optional filters like ward, has_oxygen, etc.

        Returns:
            List of available bed dictionaries
        """
        beds = self.state_cache.get("beds", [])
        available = [b for b in beds if b.get("status") == "ready"]

        if not filters:
            return available

        # Apply filters
        filtered = available

        if "ward" in filters:
            filtered = [b for b in filtered if b.get("ward") == filters["ward"]]

        if "has_oxygen" in filters:
            filtered = [
                b
                for b in filtered
                if b.get("equipment", {}).get("has_oxygen") == filters["has_oxygen"]
            ]

        if "has_ventilator" in filters:
            filtered = [
                b
                for b in filtered
                if b.get("equipment", {}).get("has_ventilator")
                == filters["has_ventilator"]
            ]

        if "is_isolation" in filters:
            filtered = [
                b
                for b in filtered
                if b.get("equipment", {}).get("is_isolation") == filters["is_isolation"]
            ]

        if "floor" in filters:
            filtered = [b for b in filtered if b.get("floor") == filters["floor"]]

        self.logger.info(f"Found {len(filtered)} beds matching filters")
        return filtered

    async def get_patient_requirements(self, patient_id: str) -> Optional[Dict]:
        """
        Get patient requirements (RULE-BASED)

        Args:
            patient_id: Patient ID

        Returns:
            Patient requirements dictionary or None
        """
        patient = await self.firebase.get_patient(patient_id)

        if not patient:
            self.logger.warning(f"Patient {patient_id} not found")
            return None

        # Extract requirements
        requirements = patient.get("requirements", {})

        # Add diagnosis and severity for context
        requirements["diagnosis"] = patient.get("diagnosis", "")
        requirements["severity"] = patient.get("severity", "moderate")
        requirements["mobility_status"] = patient.get("mobility_status", "ambulatory")

        return requirements

    async def get_staff_availability(
        self, role: str, ward: Optional[str] = None
    ) -> List[Dict]:
        """
        Get available staff by role and optional ward (RULE-BASED)

        Args:
            role: Staff role (nurse, cleaner, doctor)
            ward: Optional ward filter

        Returns:
            List of available staff
        """
        staff = self.state_cache.get("staff", [])

        # Filter by role and on-shift
        available = [
            s
            for s in staff
            if s.get("role") == role
            and s.get("is_on_shift", False)
            and s.get("current_load", 0) < 5
        ]

        # Filter by ward if specified
        if ward:
            available = [s for s in available if s.get("assigned_ward") == ward]

        # Sort by workload (least busy first)
        available.sort(key=lambda x: x.get("current_load", 0))

        self.logger.info(f"Found {len(available)} available {role}s")
        return available

    async def get_system_state(self) -> Dict[str, Any]:
        """
        Get complete system state snapshot (RULE-BASED)

        Returns:
            System state dictionary
        """
        beds = self.state_cache.get("beds", [])
        patients = self.state_cache.get("patients", [])
        staff = self.state_cache.get("staff", [])
        tasks = self.state_cache.get("tasks", [])

        return {
            "beds": {
                "total": len(beds),
                "available": len([b for b in beds if b["status"] == "ready"]),
                "occupied": len([b for b in beds if b["status"] == "occupied"]),
                "cleaning": len([b for b in beds if b["status"] == "cleaning"]),
                "maintenance": len([b for b in beds if b["status"] == "maintenance"]),
            },
            "patients": {
                "total": len(patients),
                "waiting": len([p for p in patients if p.get("status") == "waiting"]),
                "admitted": len([p for p in patients if p.get("status") == "admitted"]),
            },
            "staff": {
                "total": len(staff),
                "on_shift": len([s for s in staff if s.get("is_on_shift")]),
                "nurses": len(
                    [s for s in staff if s["role"] == "nurse" and s.get("is_on_shift")]
                ),
                "cleaners": len(
                    [
                        s
                        for s in staff
                        if s["role"] == "cleaner" and s.get("is_on_shift")
                    ]
                ),
            },
            "tasks": {
                "total": len(tasks),
                "pending": len([t for t in tasks if t["status"] == "pending"]),
                "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
            },
            "timestamp": datetime.now().isoformat(),
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get operational metrics (RULE-BASED)

        Returns:
            Metrics dictionary
        """
        return await self.firebase.get_metrics()

    # ==================== AI-POWERED METHODS (50%) ====================

    async def analyze_state_with_ai(self) -> Dict[str, Any]:
        """
        Use Gemini AI to analyze current hospital state (AI-POWERED)

        Returns:
            Analysis with alerts, bottlenecks, forecast, recommendations
        """
        try:
            self.logger.info("Running AI state analysis...")

            # Prepare state summary
            state = await self.get_system_state()
            ward_summary = self._prepare_ward_summary()

            # Build prompt
            prompt = StateManagerPrompts.STATE_ANALYSIS.format(
                total_beds=state["beds"]["total"],
                available_beds=state["beds"]["available"],
                occupied_beds=state["beds"]["occupied"],
                cleaning_beds=state["beds"]["cleaning"],
                maintenance_beds=state["beds"]["maintenance"],
                utilization_rate=round(
                    (state["beds"]["occupied"] / state["beds"]["total"] * 100)
                    if state["beds"]["total"] > 0
                    else 0,
                    1,
                ),
                total_patients=state["patients"]["total"],
                waiting_patients=state["patients"]["waiting"],
                admitted_patients=state["patients"]["admitted"],
                nurses_count=state["staff"]["nurses"],
                cleaners_count=state["staff"]["cleaners"],
                total_staff=state["staff"]["on_shift"],
                active_tasks=state["tasks"]["total"],
                pending_tasks=state["tasks"]["pending"],
                in_progress_tasks=state["tasks"]["in_progress"],
                overdue_tasks=0,  # TODO: Calculate overdue
                ward_summary=ward_summary,
            )

            # Call Gemini AI
            response = await self.gemini.generate_json_response(prompt, temperature=0.3)

            # Parse response
            if response:
                parsed = ResponseParser.parse_state_analysis_response(response)

                # Log decision
                await self.log_decision(
                    action="state_analysis",
                    input_data={"state": state},
                    output_data=parsed,
                    reasoning="AI-powered state analysis completed",
                )

                return parsed
            else:
                self.logger.warning("Empty response from AI, returning default")
                return self._default_analysis_response()

        except Exception as e:
            self.logger.error(f"Error in AI state analysis: {e}")
            return self._default_analysis_response()

    async def detect_bottlenecks(self) -> List[Dict[str, Any]]:
        """
        Detect operational bottlenecks (HYBRID: Rule-based + AI)

        Returns:
            List of bottleneck dictionaries
        """
        bottlenecks = []

        # Rule-based detection
        rule_bottlenecks = await self._detect_bottlenecks_rule_based()
        bottlenecks.extend(rule_bottlenecks)

        # AI-enhanced detection
        if rule_bottlenecks:
            ai_analysis = await self._detect_bottlenecks_ai()
            if ai_analysis:
                bottlenecks.extend(ai_analysis)

        return bottlenecks

    async def _detect_bottlenecks_rule_based(self) -> List[Dict[str, Any]]:
        """Rule-based bottleneck detection"""
        bottlenecks = []

        beds = self.state_cache.get("beds", [])
        staff = self.state_cache.get("staff", [])
        tasks = self.state_cache.get("tasks", [])

        # Check cleaning backlog
        cleaning_tasks = [
            t
            for t in tasks
            if t.get("task_type") == "cleaning" and t["status"] == "pending"
        ]
        if len(cleaning_tasks) > 5:
            severity = (
                "critical"
                if len(cleaning_tasks) > 10
                else "high"
                if len(cleaning_tasks) > 7
                else "medium"
            )
            bottlenecks.append(
                {
                    "type": "cleaning_backlog",
                    "severity": severity,
                    "count": len(cleaning_tasks),
                    "description": f"{len(cleaning_tasks)} cleaning tasks pending",
                    "recommendation": "Assign more cleaners or prioritize critical cleaning tasks",
                }
            )

        # Check staff overload
        overloaded_staff = [s for s in staff if s.get("current_load", 0) >= 5]
        if len(overloaded_staff) > 0:
            bottlenecks.append(
                {
                    "type": "staff_overload",
                    "severity": "high" if len(overloaded_staff) > 3 else "medium",
                    "count": len(overloaded_staff),
                    "description": f"{len(overloaded_staff)} staff members at maximum workload",
                    "recommendation": "Redistribute tasks or call additional staff",
                }
            )

        # Check bed capacity
        available_beds = [b for b in beds if b["status"] == "ready"]
        total_beds = len(beds)
        availability_rate = (
            (len(available_beds) / total_beds * 100) if total_beds > 0 else 0
        )

        if availability_rate < 10:
            bottlenecks.append(
                {
                    "type": "critical_capacity",
                    "severity": "critical",
                    "count": len(available_beds),
                    "description": f"Only {len(available_beds)} beds available ({availability_rate:.1f}%)",
                    "recommendation": "Expedite discharges and cleaning tasks urgently",
                }
            )
        elif availability_rate < 20:
            bottlenecks.append(
                {
                    "type": "low_capacity",
                    "severity": "high",
                    "count": len(available_beds),
                    "description": f"Low bed availability: {len(available_beds)} beds ({availability_rate:.1f}%)",
                    "recommendation": "Monitor closely and prepare for capacity issues",
                }
            )

        return bottlenecks

    async def _detect_bottlenecks_ai(self) -> List[Dict[str, Any]]:
        """AI-powered bottleneck detection for complex patterns"""
        try:
            state = await self.get_system_state()
            response = await self.gemini.detect_bottlenecks(state)

            if response and "bottlenecks" in response:
                return response["bottlenecks"]
            return []

        except Exception as e:
            self.logger.error(f"Error in AI bottleneck detection: {e}")
            return []

    def _prepare_ward_summary(self) -> str:
        """Prepare ward-level summary for prompts"""
        beds = self.state_cache.get("beds", [])

        wards = {}
        for bed in beds:
            ward = bed.get("ward", "Unknown")
            if ward not in wards:
                wards[ward] = {"total": 0, "available": 0, "occupied": 0}

            wards[ward]["total"] += 1
            if bed["status"] == "ready":
                wards[ward]["available"] += 1
            elif bed["status"] == "occupied":
                wards[ward]["occupied"] += 1

        summary_lines = []
        for ward, stats in wards.items():
            occupancy = (
                (stats["occupied"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            summary_lines.append(
                f"  - {ward}: {stats['available']}/{stats['total']} available ({occupancy:.0f}% occupied)"
            )

        return "\n".join(summary_lines) if summary_lines else "  No ward data available"

    def _default_analysis_response(self) -> Dict[str, Any]:
        """Default response when AI fails"""
        return {
            "critical_alerts": [],
            "bottlenecks": [],
            "capacity_forecast": {
                "next_4_hours": "Unable to generate forecast",
                "bed_availability_trend": "stable",
                "staffing_adequacy": "unknown",
            },
            "recommendations": ["Refresh data and try again"],
        }

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "get_available_beds",
            "get_patient_requirements",
            "get_staff_availability",
            "get_system_state",
            "analyze_state",
            "detect_bottlenecks",
            "get_metrics",
        ]
