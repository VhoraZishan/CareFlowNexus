"""
Task Coordinator Agent (Communicator Agent) for CareFlow Nexus
Agent 3: Assigns tasks to staff and orchestrates workflows

This agent is 50% rule-based (staff selection, task creation) and 50% AI (reasoning, escalation)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from base_agent import BaseAgent
from prompts.prompt_templates import TaskCoordinatorPrompts
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService
from utils.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class CommunicatorAgent(BaseAgent):
    """
    Task Coordinator Agent - Assigns tasks and orchestrates workflows

    Responsibilities:
    - Create tasks for bed assignments, cleaning, etc.
    - Assign tasks to optimal staff (rule-based + AI)
    - Orchestrate multi-step workflows
    - Monitor task progress
    - Handle delays and escalations
    """

    # Workflow templates
    WORKFLOWS = {
        "bed_assignment": [
            {
                "task_type": "cleaning",
                "role": "cleaner",
                "priority": "high",
                "estimated_duration": 30,
                "description_template": "Clean and sanitize bed {bed_number} in {ward}",
            },
            {
                "task_type": "bed_prep",
                "role": "nurse",
                "priority": "high",
                "estimated_duration": 15,
                "description_template": "Prepare bed {bed_number} for patient {patient_name}",
                "depends_on": "cleaning",
            },
            {
                "task_type": "patient_transfer",
                "role": "nurse",
                "priority": "high",
                "estimated_duration": 20,
                "description_template": "Transfer patient {patient_name} to bed {bed_number}",
                "depends_on": "bed_prep",
            },
        ],
        "discharge": [
            {
                "task_type": "patient_discharge",
                "role": "nurse",
                "priority": "normal",
                "estimated_duration": 30,
                "description_template": "Process discharge for patient {patient_name} from bed {bed_number}",
            },
            {
                "task_type": "cleaning",
                "role": "cleaner",
                "priority": "high",
                "estimated_duration": 30,
                "description_template": "Deep clean bed {bed_number} after discharge",
                "depends_on": "patient_discharge",
            },
            {
                "task_type": "bed_prep",
                "role": "nurse",
                "priority": "normal",
                "estimated_duration": 15,
                "description_template": "Prepare bed {bed_number} for next patient",
                "depends_on": "cleaning",
            },
        ],
        "bed_cleaning": [
            {
                "task_type": "cleaning",
                "role": "cleaner",
                "priority": "high",
                "estimated_duration": 30,
                "description_template": "Clean bed {bed_number} in {ward}",
            }
        ],
    }

    def __init__(
        self,
        firebase_service: FirebaseService,
        gemini_service: GeminiService,
        memory_agent,
        max_staff_workload: int = 5,
    ):
        """
        Initialize Task Coordinator Agent

        Args:
            firebase_service: Firebase service instance
            gemini_service: Gemini AI service instance
            memory_agent: Memory agent for state queries
            max_staff_workload: Maximum tasks per staff member
        """
        super().__init__(
            agent_id="task_coordinator_001",
            agent_type="task_coordinator",
            firebase_service=firebase_service,
            gemini_service=gemini_service,
        )

        self.memory_agent = memory_agent
        self.max_staff_workload = max_staff_workload

        self.logger.info("Task Coordinator Agent initialized")

    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task coordination requests

        Args:
            request_data: Request with 'type' and parameters

        Returns:
            Response dictionary
        """
        try:
            request_type = request_data.get("type", "")

            if request_type == "initiate_workflow":
                workflow_type = request_data.get("workflow_type")
                context = request_data.get("context", {})
                result = await self.initiate_workflow(workflow_type, context)
                return self.format_response(True, result, "Workflow initiated")

            elif request_type == "create_task":
                task_data = request_data.get("task_data", {})
                result = await self.create_and_assign_task(task_data)
                return self.format_response(True, result, "Task created")

            elif request_type == "assign_staff":
                task_data = request_data.get("task_data", {})
                result = await self.assign_optimal_staff(task_data)
                return self.format_response(True, result, "Staff assigned")

            elif request_type == "check_task_progress":
                result = await self.check_task_progress()
                return self.format_response(True, result, "Task progress checked")

            elif request_type == "handle_delayed_task":
                task_id = request_data.get("task_id")
                result = await self.handle_delayed_task(task_id)
                return self.format_response(True, result, "Delayed task handled")

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

    # ==================== WORKFLOW ORCHESTRATION ====================

    async def initiate_workflow(
        self, workflow_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Initiate a multi-step workflow

        Args:
            workflow_type: Type of workflow (bed_assignment, discharge, etc.)
            context: Context data (patient_id, bed_id, etc.)

        Returns:
            Result with created task IDs
        """
        try:
            self.logger.info(f"Initiating workflow: {workflow_type}")

            if workflow_type not in self.WORKFLOWS:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            workflow_template = self.WORKFLOWS[workflow_type]

            # Get patient and bed info for descriptions
            patient_id = context.get("patient_id")
            bed_id = context.get("bed_id")

            patient = None
            bed = None

            if patient_id:
                patient = await self.firebase.get_patient(patient_id)

            if bed_id:
                bed = await self.firebase.get_bed(bed_id)

            # Create tasks
            created_tasks = []
            for task_template in workflow_template:
                # Check if task has dependencies
                depends_on = task_template.get("depends_on")
                if depends_on:
                    # For now, just create all tasks immediately
                    # In production, implement dependency checking
                    pass

                # Format description
                description = task_template["description_template"].format(
                    patient_name=patient.get("name", "Patient")
                    if patient
                    else "Patient",
                    bed_number=bed.get("bed_number", "N/A") if bed else "N/A",
                    ward=bed.get("ward", "N/A") if bed else "N/A",
                )

                # Create task data
                task_data = {
                    "task_type": task_template["task_type"],
                    "description": description,
                    "priority": task_template["priority"],
                    "estimated_duration": task_template["estimated_duration"],
                    "bed_id": bed_id,
                    "patient_id": patient_id,
                    "workflow_type": workflow_type,
                    "assigned_by": "AI",
                }

                # Create and assign task
                task_result = await self.create_and_assign_task(task_data)
                created_tasks.append(task_result)

            # Log workflow initiation
            await self.log_decision(
                action="initiate_workflow",
                input_data={"workflow_type": workflow_type, "context": context},
                output_data={"tasks_created": len(created_tasks)},
                reasoning=f"Initiated {workflow_type} workflow with {len(created_tasks)} tasks",
            )

            return {
                "workflow_type": workflow_type,
                "tasks_created": created_tasks,
                "total_tasks": len(created_tasks),
            }

        except Exception as e:
            self.logger.error(f"Error initiating workflow: {e}")
            raise

    # ==================== TASK CREATION & ASSIGNMENT ====================

    async def create_and_assign_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create task and assign to optimal staff member

        Args:
            task_data: Task information

        Returns:
            Created task with assignment details
        """
        try:
            # Get required role
            task_type = task_data.get("task_type")
            required_role = self._get_required_role(task_type)

            # Get bed info for ward context
            bed_id = task_data.get("bed_id")
            ward = None
            if bed_id:
                bed = await self.firebase.get_bed(bed_id)
                if bed:
                    ward = bed.get("ward")

            # Assign optimal staff (50% rule-based, 50% AI)
            assignment = await self.assign_optimal_staff(
                {
                    "task_type": task_type,
                    "required_role": required_role,
                    "ward": ward,
                    "priority": task_data.get("priority", "normal"),
                    "description": task_data.get("description", ""),
                }
            )

            if not assignment.get("staff_id"):
                # No staff available
                self.logger.warning(f"No staff available for {task_type}")
                task_data["assigned_to"] = None
                task_data["status"] = "pending"
            else:
                task_data["assigned_to"] = assignment["staff_id"]
                task_data["status"] = "pending"

            # Create task in Firebase
            task_id = await self.firebase.create_task(task_data)

            if not task_id:
                raise Exception("Failed to create task in Firebase")

            result = {
                "task_id": task_id,
                "task_type": task_type,
                "assigned_to": assignment.get("staff_id"),
                "staff_name": assignment.get("staff_name"),
                "reasoning": assignment.get("reasoning", ""),
                "priority": task_data.get("priority"),
                "description": task_data.get("description"),
            }

            self.logger.info(
                f"Created task {task_id} and assigned to {assignment.get('staff_name', 'No one (pending)')}"
            )

            # Log decision
            await self.log_decision(
                action="create_task",
                input_data=task_data,
                output_data=result,
                reasoning=assignment.get("reasoning", "Task created"),
            )

            return result

        except Exception as e:
            self.logger.error(f"Error creating and assigning task: {e}")
            raise

    # ==================== STAFF ASSIGNMENT (HYBRID 50/50) ====================

    async def assign_optimal_staff(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign optimal staff member to task using hybrid approach

        Args:
            task_info: Task information

        Returns:
            Assignment dictionary with staff_id and reasoning
        """
        try:
            required_role = task_info.get("required_role")
            ward = task_info.get("ward")

            # Step 1: Get available staff from memory agent (rule-based)
            staff_response = await self.memory_agent.process(
                {"type": "get_staff_availability", "role": required_role, "ward": ward}
            )
            available_staff = staff_response.get("data", [])

            if not available_staff:
                self.logger.warning(f"No available {required_role} staff")
                return {
                    "staff_id": None,
                    "staff_name": None,
                    "reasoning": f"No available {required_role} staff",
                    "confidence": 0,
                }

            # Step 2: Rule-based scoring
            scored_staff = self._score_staff_rule_based(available_staff, task_info)

            # Step 3: Get AI recommendation (top 5 candidates)
            top_candidates = scored_staff[:5]
            ai_recommendation = await self._get_ai_staff_recommendation(
                task_info, top_candidates
            )

            # Step 4: Combine rule-based and AI decision
            final_assignment = self._combine_staff_assignment(
                scored_staff, ai_recommendation
            )

            return final_assignment

        except Exception as e:
            self.logger.error(f"Error assigning staff: {e}")
            # Fallback to first available staff
            if available_staff:
                return {
                    "staff_id": available_staff[0].get("id"),
                    "staff_name": available_staff[0].get("name"),
                    "reasoning": "Fallback assignment to first available staff",
                    "confidence": 50,
                }
            return {
                "staff_id": None,
                "staff_name": None,
                "reasoning": "No staff available",
                "confidence": 0,
            }

    def _score_staff_rule_based(
        self, staff_list: List[Dict], task_info: Dict
    ) -> List[Dict]:
        """
        Score staff members using rule-based criteria

        Scoring:
        - Workload (0-5 tasks): 40 points (fewer tasks = higher score)
        - Ward match: 30 points
        - Recent activity: 20 points
        - Bonus: 10 points

        Args:
            staff_list: List of available staff
            task_info: Task information

        Returns:
            Sorted list of staff with scores
        """
        task_ward = task_info.get("ward")
        scored_staff = []

        for staff in staff_list:
            score = 0

            # 1. Workload score (40 points max)
            current_load = staff.get("current_load", 0)
            workload_score = max(0, 40 - (current_load * 8))  # 8 points per task
            score += workload_score

            # 2. Ward match (30 points)
            staff_ward = staff.get("assigned_ward")
            if task_ward and staff_ward == task_ward:
                score += 30
            elif task_ward and staff_ward:
                score += 10  # Different ward but still assigned somewhere
            else:
                score += 15  # No ward assignment

            # 3. Recent activity (20 points)
            # For now, give everyone 15 points (would need task history)
            score += 15

            # 4. Bonus points (10 points)
            score += 10

            scored_staff.append(
                {
                    **staff,
                    "rule_score": score,
                }
            )

        # Sort by score (highest first)
        scored_staff.sort(key=lambda x: x["rule_score"], reverse=True)

        return scored_staff

    async def _get_ai_staff_recommendation(
        self, task_info: Dict, candidates: List[Dict]
    ) -> Dict[str, Any]:
        """
        Get AI recommendation for staff assignment

        Args:
            task_info: Task information
            candidates: Top staff candidates from rule-based scoring

        Returns:
            AI recommendation dictionary
        """
        try:
            # Prepare candidates for AI
            candidates_for_ai = []
            for staff in candidates:
                candidates_for_ai.append(
                    {
                        "staff_id": staff.get("id"),
                        "name": staff.get("name"),
                        "role": staff.get("role"),
                        "current_load": staff.get("current_load", 0),
                        "assigned_ward": staff.get("assigned_ward"),
                        "rule_score": staff.get("rule_score"),
                    }
                )

            # Get system state for context
            state_response = await self.memory_agent.process(
                {"type": "get_system_state"}
            )
            state = state_response.get("data", {})

            # Build prompt
            prompt = TaskCoordinatorPrompts.STAFF_ASSIGNMENT.format(
                task_id="TBD",
                task_type=task_info.get("task_type"),
                description=task_info.get("description", ""),
                priority=task_info.get("priority", "normal"),
                ward=task_info.get("ward", "Unknown"),
                bed_number="TBD",
                duration=task_info.get("estimated_duration", 30),
                patient_name="Patient",
                staff_json=self._format_staff_for_prompt(candidates_for_ai),
                required_role=task_info.get("required_role"),
                current_time=datetime.now().strftime("%H:%M"),
                activity_level="normal",
                pending_tasks_count=state.get("tasks", {}).get("pending", 0),
            )

            # Call Gemini AI
            response = await self.gemini.generate_json_response(prompt, temperature=0.5)

            if response:
                parsed = ResponseParser.parse_staff_assignment_response(response)
                self.logger.info(
                    f"AI recommended staff: {parsed.get('staff_name')} with {parsed.get('confidence')}% confidence"
                )
                return parsed

            return {}

        except Exception as e:
            self.logger.error(f"Error getting AI staff recommendation: {e}")
            return {}

    def _format_staff_for_prompt(self, staff_list: List[Dict]) -> str:
        """Format staff list for AI prompt"""
        lines = []
        for i, staff in enumerate(staff_list, 1):
            lines.append(
                f"{i}. {staff.get('name')} ({staff.get('role')})\n"
                f"   Current Workload: {staff.get('current_load', 0)} tasks\n"
                f"   Ward: {staff.get('assigned_ward', 'Any')}\n"
                f"   Rule Score: {staff.get('rule_score', 0)}/100"
            )
        return "\n\n".join(lines)

    def _combine_staff_assignment(
        self, rule_based_staff: List[Dict], ai_recommendation: Dict
    ) -> Dict[str, Any]:
        """
        Combine rule-based and AI staff assignment (50/50 approach)

        Args:
            rule_based_staff: Staff sorted by rule-based score
            ai_recommendation: AI recommendation

        Returns:
            Final assignment decision
        """
        # Get AI recommended staff ID
        ai_staff_id = ai_recommendation.get("recommended_staff_id")

        # If AI has a recommendation, use it
        if ai_staff_id:
            # Find the staff member
            for staff in rule_based_staff:
                if staff.get("id") == ai_staff_id:
                    return {
                        "staff_id": staff.get("id"),
                        "staff_name": staff.get("name"),
                        "reasoning": ai_recommendation.get(
                            "reasoning", "AI recommendation"
                        ),
                        "workload_impact": ai_recommendation.get("workload_impact", ""),
                        "confidence": ai_recommendation.get("confidence", 75),
                        "method": "AI-selected",
                    }

        # Fallback to rule-based top choice
        if rule_based_staff:
            top_staff = rule_based_staff[0]
            return {
                "staff_id": top_staff.get("id"),
                "staff_name": top_staff.get("name"),
                "reasoning": f"Selected based on lowest workload ({top_staff.get('current_load', 0)} tasks) and ward proximity",
                "workload_impact": f"Workload will increase from {top_staff.get('current_load', 0)} to {top_staff.get('current_load', 0) + 1} tasks",
                "confidence": 70,
                "method": "Rule-based",
            }

        return {
            "staff_id": None,
            "staff_name": None,
            "reasoning": "No staff available",
            "confidence": 0,
            "method": "None",
        }

    # ==================== TASK MONITORING ====================

    async def check_task_progress(self) -> Dict[str, Any]:
        """
        Check progress of all active tasks

        Returns:
            Task progress summary with delays
        """
        try:
            # Get all active tasks
            tasks = await self.firebase.get_tasks(
                {"status": ["pending", "in_progress"]}
            )

            delayed_tasks = []
            on_track_tasks = []
            current_time = datetime.now()

            for task in tasks:
                created_at = task.get("created_at")
                estimated_duration = task.get("estimated_duration", 30)

                # Calculate expected completion time
                if created_at:
                    # Convert Firestore timestamp if needed
                    if hasattr(created_at, "timestamp"):
                        created_at = datetime.fromtimestamp(created_at.timestamp())

                    expected_completion = created_at + timedelta(
                        minutes=estimated_duration
                    )

                    if current_time > expected_completion:
                        delay_minutes = (
                            current_time - expected_completion
                        ).total_seconds() / 60
                        delayed_tasks.append(
                            {
                                "task_id": task.get("id"),
                                "task_type": task.get("task_type"),
                                "delay_minutes": int(delay_minutes),
                                "priority": task.get("priority"),
                                "assigned_to": task.get("assigned_to"),
                            }
                        )
                    else:
                        on_track_tasks.append(task.get("id"))

            result = {
                "total_active_tasks": len(tasks),
                "on_track": len(on_track_tasks),
                "delayed": len(delayed_tasks),
                "delayed_tasks": delayed_tasks,
            }

            self.logger.info(
                f"Task progress: {len(on_track_tasks)} on track, {len(delayed_tasks)} delayed"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error checking task progress: {e}")
            return {"error": str(e)}

    async def handle_delayed_task(self, task_id: str) -> Dict[str, Any]:
        """
        Handle a delayed task (escalation logic)

        Args:
            task_id: Task ID

        Returns:
            Action taken
        """
        try:
            task = await self.firebase.get_task(task_id)

            if not task:
                return {"action": "none", "reason": "Task not found"}

            # Simple escalation logic
            priority = task.get("priority", "normal")

            if priority == "high" or priority == "urgent":
                # Escalate to supervisor
                action = "escalated"
                message = f"High priority task {task_id} is delayed"

                await self.firebase.log_event(
                    {
                        "entity_type": "task_escalation",
                        "entity_id": task_id,
                        "action": "escalate_to_supervisor",
                        "triggered_by": self.agent_type,
                        "details": {"task": task, "reason": "delayed"},
                    }
                )

            else:
                # Increase priority
                action = "priority_increased"
                new_priority = "high" if priority == "normal" else "urgent"
                await self.firebase.update_task_status(
                    task_id, task.get("status"), f"Priority increased to {new_priority}"
                )
                message = f"Task priority increased to {new_priority}"

            return {"action": action, "message": message, "task_id": task_id}

        except Exception as e:
            self.logger.error(f"Error handling delayed task: {e}")
            return {"action": "error", "reason": str(e)}

    # ==================== HELPER METHODS ====================

    def _get_required_role(self, task_type: str) -> str:
        """Get required staff role for task type"""
        role_map = {
            "cleaning": "cleaner",
            "bed_prep": "nurse",
            "patient_transfer": "nurse",
            "patient_discharge": "nurse",
            "medication": "nurse",
            "examination": "doctor",
        }
        return role_map.get(task_type, "nurse")

    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "initiate_workflow",
            "create_task",
            "assign_staff",
            "check_task_progress",
            "handle_delayed_task",
            "orchestrate_workflows",
        ]
