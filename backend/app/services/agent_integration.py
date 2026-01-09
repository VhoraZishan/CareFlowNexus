"""
Agent Integration Service for CareFlow Nexus Backend
Integrates the AI agents (Memory, Bed Allocator, Communicator) with the existing FastAPI backend
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add agents directory to Python path
AGENTS_DIR = Path(__file__).parent.parent.parent.parent / "agents"
sys.path.insert(0, str(AGENTS_DIR))

# Import agents
from allocator_agent import BedAllocatorAgent
from communicator_agent import CommunicatorAgent
from config import config as agent_config
from memory_agent import MemoryAgent
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService


class AgentIntegration:
    """
    Integration layer between backend API and AI agents
    Provides a clean interface for the backend to call agent functions
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to ensure only one agent instance"""
        if cls._instance is None:
            cls._instance = super(AgentIntegration, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize agent integration (only once)"""
        if not AgentIntegration._initialized:
            self.firebase_service: Optional[FirebaseService] = None
            self.gemini_service: Optional[GeminiService] = None
            self.memory_agent: Optional[MemoryAgent] = None
            self.bed_allocator_agent: Optional[BedAllocatorAgent] = None
            self.communicator_agent: Optional[CommunicatorAgent] = None
            AgentIntegration._initialized = True

    async def initialize(self):
        """Initialize all AI agents"""
        try:
            print("Initializing AI Agents...")

            # Initialize Firebase service
            self.firebase_service = FirebaseService(
                service_account_path=agent_config.firebase.service_account_path
            )
            print("✓ Firebase service initialized")

            # Initialize Gemini service
            self.gemini_service = GeminiService(
                api_key=agent_config.gemini.api_key,
                model_name=agent_config.gemini.model_name,
            )
            print("✓ Gemini AI service initialized")

            # Initialize Memory Agent
            self.memory_agent = MemoryAgent(
                firebase_service=self.firebase_service,
                gemini_service=self.gemini_service,
                refresh_interval=agent_config.agent.state_refresh_interval,
            )
            await self.memory_agent.initialize()
            print("✓ Memory Agent initialized")

            # Initialize Bed Allocator Agent
            self.bed_allocator_agent = BedAllocatorAgent(
                firebase_service=self.firebase_service,
                gemini_service=self.gemini_service,
                memory_agent=self.memory_agent,
                rule_weight=agent_config.agent.rule_weight,
            )
            print("✓ Bed Allocator Agent initialized")

            # Initialize Communicator Agent
            self.communicator_agent = CommunicatorAgent(
                firebase_service=self.firebase_service,
                gemini_service=self.gemini_service,
                memory_agent=self.memory_agent,
                max_staff_workload=agent_config.agent.max_staff_workload,
            )
            print("✓ Communicator Agent initialized")

            print("All AI agents ready!")
            return True

        except Exception as e:
            print(f"Error initializing agents: {e}")
            raise

    def is_ready(self) -> bool:
        """Check if all agents are initialized"""
        return all(
            [
                self.firebase_service is not None,
                self.gemini_service is not None,
                self.memory_agent is not None,
                self.bed_allocator_agent is not None,
                self.communicator_agent is not None,
            ]
        )

    # ==================== BED ALLOCATION AGENT ====================

    async def call_bed_agent(
        self,
        patient: Dict[str, Any],
        doctor_input: Dict[str, Any],
        available_beds: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Call Bed Allocation Agent (API Contract compliant)

        Input format (from API contract):
        {
            "patient": {...},
            "doctor_input": {
                "diagnosis": "Pneumonia",
                "special_instructions": "Oxygen support"
            },
            "available_beds": [...]
        }

        Output format:
        {
            "recommended_bed_id": "bed22",
            "reason": "Supports oxygen",
            "recommendations": [top 3 beds with scores],
            "confidence": 85
        }
        """
        try:
            if not self.is_ready():
                raise RuntimeError("Agents not initialized")

            # Update patient with diagnosis information
            patient_id = patient.get("patient_id")

            # Temporarily store diagnosis in patient record for agent processing
            await self.firebase_service.update_patient(
                patient_id,
                {
                    "diagnosis": doctor_input.get("diagnosis"),
                    "severity": self._infer_severity(doctor_input.get("diagnosis", "")),
                    "requirements": self._extract_basic_requirements(doctor_input),
                },
            )

            # Call Bed Allocator Agent
            result = await self.bed_allocator_agent.process({"patient_id": patient_id})

            if not result.get("success"):
                return {
                    "recommended_bed_id": None,
                    "reason": result.get("message", "No suitable beds found"),
                    "recommendations": [],
                    "confidence": 0,
                }

            data = result.get("data", {})
            recommendations = data.get("recommendations", [])

            # Format response according to API contract
            return {
                "recommended_bed_id": recommendations[0].get("bed_id")
                if recommendations
                else None,
                "reason": recommendations[0].get("reasoning")
                if recommendations
                else "No beds available",
                "recommendations": [
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
                "confidence": data.get("confidence", 0),
            }

        except Exception as e:
            print(f"Error in bed agent: {e}")
            return {
                "recommended_bed_id": None,
                "reason": f"Error: {str(e)}",
                "recommendations": [],
                "confidence": 0,
            }

    # ==================== STAFF ASSIGNMENT AGENTS ====================

    async def call_cleaner_agent(
        self, bed_id: str, available_cleaners: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call Cleaner Assignment Agent (API Contract compliant)

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
            if not self.is_ready():
                raise RuntimeError("Agents not initialized")

            # Get bed information
            bed = await self.firebase_service.get_bed(bed_id)

            # Use Communicator Agent to assign staff
            # Create a cleaning task
            task_data = {
                "task_type": "cleaning",
                "description": f"Clean bed {bed.get('bed_id')} in {bed.get('ward')}",
                "bed_id": bed_id,
                "priority": "high",
                "role": "cleaner",
            }

            # The communicator agent will select the best cleaner
            result = await self.communicator_agent.process(
                {"type": "assign_staff", "task_data": task_data}
            )

            if result.get("success"):
                assignment = result.get("data", {})
                return {
                    "selected_cleaner_id": assignment.get("staff_id"),
                    "reason": assignment.get(
                        "reasoning", "Selected based on workload and availability"
                    ),
                }
            else:
                # Fallback: select first available cleaner
                if available_cleaners:
                    return {
                        "selected_cleaner_id": available_cleaners[0].get("user_id"),
                        "reason": "First available cleaner",
                    }
                return {"selected_cleaner_id": None, "reason": "No cleaners available"}

        except Exception as e:
            print(f"Error in cleaner agent: {e}")
            # Fallback
            if available_cleaners:
                return {
                    "selected_cleaner_id": available_cleaners[0].get("user_id"),
                    "reason": f"Fallback assignment due to error",
                }
            return {"selected_cleaner_id": None, "reason": f"Error: {str(e)}"}

    async def call_nurse_agent(
        self,
        patient: Dict[str, Any],
        bed: Dict[str, Any],
        available_nurses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Call Nurse Assignment Agent (API Contract compliant)

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
            if not self.is_ready():
                raise RuntimeError("Agents not initialized")

            # Use Communicator Agent to assign nurse
            task_data = {
                "task_type": "nursing",
                "description": f"Prepare bed {bed.get('bed_id')} for patient {patient.get('name')}",
                "bed_id": bed.get("bed_id"),
                "patient_id": patient.get("patient_id"),
                "priority": "high",
                "role": "nurse",
            }

            result = await self.communicator_agent.process(
                {"type": "assign_staff", "task_data": task_data}
            )

            if result.get("success"):
                assignment = result.get("data", {})
                return {
                    "selected_nurse_id": assignment.get("staff_id"),
                    "reason": assignment.get(
                        "reasoning", "Selected based on workload and specialization"
                    ),
                }
            else:
                # Fallback
                if available_nurses:
                    return {
                        "selected_nurse_id": available_nurses[0].get("user_id"),
                        "reason": "First available nurse",
                    }
                return {"selected_nurse_id": None, "reason": "No nurses available"}

        except Exception as e:
            print(f"Error in nurse agent: {e}")
            # Fallback
            if available_nurses:
                return {
                    "selected_nurse_id": available_nurses[0].get("user_id"),
                    "reason": f"Fallback assignment",
                }
            return {"selected_nurse_id": None, "reason": f"Error: {str(e)}"}

    # ==================== TASK CREATION ====================

    async def create_admission_tasks(
        self,
        patient_id: str,
        bed_id: str,
        nurse_id: Optional[str] = None,
        cleaner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create all tasks for patient admission workflow
        Uses Communicator Agent to orchestrate the workflow
        """
        try:
            if not self.is_ready():
                raise RuntimeError("Agents not initialized")

            # Use Communicator Agent's workflow orchestration
            result = await self.communicator_agent.process(
                {
                    "type": "initiate_workflow",
                    "workflow_type": "bed_assignment",
                    "context": {"patient_id": patient_id, "bed_id": bed_id},
                }
            )

            if result.get("success"):
                tasks = result.get("data", {}).get("tasks_created", [])
                return {"tasks_created": len(tasks), "tasks": tasks}
            else:
                return {"tasks_created": 0, "tasks": []}

        except Exception as e:
            print(f"Error creating tasks: {e}")
            return {"tasks_created": 0, "tasks": [], "error": str(e)}

    # ==================== HELPER METHODS ====================

    def _extract_basic_requirements(
        self, doctor_input: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                word in combined_text
                for word in ["isolation", "infectious", "contagious"]
            ),
        }

        return requirements

    def _infer_severity(self, diagnosis: str) -> str:
        """Infer severity from diagnosis text"""
        diagnosis_lower = diagnosis.lower()

        if any(
            word in diagnosis_lower
            for word in ["critical", "severe", "emergency", "acute"]
        ):
            return "critical"
        elif any(word in diagnosis_lower for word in ["moderate", "significant"]):
            return "high"
        elif any(word in diagnosis_lower for word in ["mild", "minor"]):
            return "low"
        else:
            return "moderate"

    async def get_system_state(self) -> Dict[str, Any]:
        """Get current hospital system state from Memory Agent"""
        if not self.is_ready():
            return {}

        result = await self.memory_agent.process({"type": "get_system_state"})
        return result.get("data", {})

    async def get_available_beds(
        self, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Get available beds from Memory Agent"""
        if not self.is_ready():
            return []

        result = await self.memory_agent.process(
            {"type": "get_available_beds", "filters": filters or {}}
        )
        return result.get("data", [])


# Global agent integration instance
agent_integration = AgentIntegration()


# ==================== CONVENIENCE FUNCTIONS ====================


async def initialize_agents():
    """Initialize all agents - call this on backend startup"""
    await agent_integration.initialize()


def get_agent_integration() -> AgentIntegration:
    """Get the global agent integration instance"""
    return agent_integration


# ==================== SYNCHRONOUS WRAPPER (for existing backend) ====================


def call_bed_agent(
    patient: Dict, doctor_input: Dict, available_beds: List[Dict]
) -> Dict:
    """Synchronous wrapper for bed agent (backward compatible)"""
    return asyncio.run(
        agent_integration.call_bed_agent(patient, doctor_input, available_beds)
    )


def call_cleaner_agent(bed_id: str, available_cleaners: List[Dict]) -> Dict:
    """Synchronous wrapper for cleaner agent (backward compatible)"""
    return asyncio.run(agent_integration.call_cleaner_agent(bed_id, available_cleaners))


def call_nurse_agent(patient: Dict, bed: Dict, available_nurses: List[Dict]) -> Dict:
    """Synchronous wrapper for nurse agent (backward compatible)"""
    return asyncio.run(
        agent_integration.call_nurse_agent(patient, bed, available_nurses)
    )
