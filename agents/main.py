"""
Main Entry Point for CareFlow Nexus AI Agents
Initializes and runs all three agents: Memory Agent, Bed Allocator Agent, and Communicator Agent
"""

import asyncio
import logging
import sys
from datetime import datetime

from allocator_agent import BedAllocatorAgent
from communicator_agent import CommunicatorAgent
from config import config
from memory_agent import MemoryAgent
from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService


# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, config.system.log_level, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"careflow_agents_{datetime.now().strftime('%Y%m%d')}.log"
            ),
        ],
    )


logger = logging.getLogger(__name__)


class CareFlowAgentSystem:
    """Main system that manages all three agents"""

    def __init__(self):
        """Initialize the agent system"""
        self.firebase_service = None
        self.gemini_service = None
        self.memory_agent = None
        self.bed_allocator_agent = None
        self.communicator_agent = None

    async def initialize(self):
        """Initialize all services and agents"""
        try:
            logger.info("=" * 60)
            logger.info("CareFlow Nexus AI Agent System")
            logger.info("=" * 60)
            logger.info(f"Environment: {config.system.environment}")
            logger.info(f"Gemini Model: {config.gemini.model_name}")
            logger.info(
                f"Agent Weights: Rule={config.agent.rule_weight * 100}%, AI={config.agent.ai_weight * 100}%"
            )
            logger.info("=" * 60)

            # Validate configuration
            logger.info("Validating configuration...")
            if not config.validate():
                raise Exception("Configuration validation failed")
            logger.info("OK Configuration valid")

            # Initialize Firebase service
            logger.info("Initializing Firebase service...")
            self.firebase_service = FirebaseService(
                service_account_path=config.firebase.service_account_path
            )
            logger.info("OK Firebase service initialized")

            # Initialize Gemini service
            logger.info("Initializing Gemini AI service...")
            self.gemini_service = GeminiService(
                api_key=config.gemini.api_key, model_name=config.gemini.model_name
            )
            logger.info("OK Gemini AI service initialized")

            # Initialize Agent 1: Memory Agent (State Manager)
            logger.info("\nInitializing Agent 1: Memory Agent (State Manager)...")
            self.memory_agent = MemoryAgent(
                firebase_service=self.firebase_service,
                gemini_service=self.gemini_service,
                refresh_interval=config.agent.state_refresh_interval,
            )
            await self.memory_agent.initialize()
            logger.info("OK Memory Agent initialized and loaded hospital data")

            # Initialize Agent 2: Bed Allocator Agent
            logger.info("\nInitializing Agent 2: Bed Allocator Agent...")
            self.bed_allocator_agent = BedAllocatorAgent(
                firebase_service=self.firebase_service,
                gemini_service=self.gemini_service,
                memory_agent=self.memory_agent,
                rule_weight=config.agent.rule_weight,
            )
            logger.info("OK Bed Allocator Agent initialized")

            # Initialize Agent 3: Communicator Agent (Task Coordinator)
            logger.info(
                "\nInitializing Agent 3: Communicator Agent (Task Coordinator)..."
            )
            self.communicator_agent = CommunicatorAgent(
                firebase_service=self.firebase_service,
                gemini_service=self.gemini_service,
                memory_agent=self.memory_agent,
                max_staff_workload=config.agent.max_staff_workload,
            )
            logger.info("OK Communicator Agent initialized")

            logger.info("\n" + "=" * 60)
            logger.info("OK ALL AGENTS INITIALIZED SUCCESSFULLY")
            logger.info("=" * 60 + "\n")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize agent system: {e}")
            raise

    async def handle_new_patient_admission(self, patient_id: str):
        """
        Handle complete patient admission workflow

        This demonstrates the full workflow:
        1. Memory Agent provides patient data
        2. Bed Allocator Agent recommends beds
        3. Receptionist confirms
        4. Communicator Agent creates tasks for staff

        Args:
            patient_id: Patient ID
        """
        try:
            logger.info("\n" + "=" * 60)
            logger.info(f"PROCESSING PATIENT ADMISSION: {patient_id}")
            logger.info("=" * 60)

            # Step 1: Get patient info from Memory Agent
            logger.info("\n[Step 1] Fetching patient information...")
            patient = await self.firebase_service.get_patient(patient_id)
            if not patient:
                logger.error(f"Patient {patient_id} not found")
                return {"success": False, "message": "Patient not found"}

            logger.info(f"Patient: {patient.get('name')}")
            logger.info(f"Diagnosis: {patient.get('diagnosis', 'No diagnosis')}")
            logger.info(f"Severity: {patient.get('severity', 'Unknown')}")

            # Step 2: Get bed recommendations from Bed Allocator Agent
            logger.info(
                "\n[Step 2] Requesting bed allocation from Bed Allocator Agent..."
            )
            allocation_response = await self.bed_allocator_agent.process(
                {"patient_id": patient_id}
            )

            if not allocation_response.get("success"):
                logger.error(
                    f"Bed allocation failed: {allocation_response.get('message')}"
                )
                return allocation_response

            allocation_data = allocation_response.get("data", {})
            recommendations = allocation_data.get("recommendations", [])

            if not recommendations:
                logger.warning("No bed recommendations available")
                return {"success": False, "message": "No suitable beds found"}

            # Display recommendations
            logger.info(
                f"\n🤖 AI Bed Recommendations (Confidence: {allocation_data.get('confidence')}%):\n"
            )
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"{i}. Bed {rec.get('bed_number')} - {rec.get('ward')}")
                logger.info(f"   Score: {rec.get('score')}/100")
                logger.info(f"   Reasoning: {rec.get('reasoning')}")
                logger.info(f"   Pros: {', '.join(rec.get('pros', []))}")
                if rec.get("cons"):
                    logger.info(f"   Cons: {', '.join(rec.get('cons', []))}")
                logger.info("")

            # Step 3: Simulate receptionist confirmation (auto-confirm top recommendation)
            logger.info("\n[Step 3] Receptionist confirms bed assignment...")
            confirmed_bed = recommendations[0]
            bed_id = confirmed_bed.get("bed_id")
            bed_number = confirmed_bed.get("bed_number")

            logger.info(f"OK Confirmed: Bed {bed_number}")

            # Assign bed to patient
            await self.firebase_service.assign_bed_to_patient(bed_id, patient_id)
            logger.info("OK Bed assigned in database")

            # Step 4: Create tasks using Communicator Agent
            logger.info("\n[Step 4] Creating tasks for staff via Communicator Agent...")
            workflow_response = await self.communicator_agent.process(
                {
                    "type": "initiate_workflow",
                    "workflow_type": "bed_assignment",
                    "context": {"patient_id": patient_id, "bed_id": bed_id},
                }
            )

            if workflow_response.get("success"):
                workflow_data = workflow_response.get("data", {})
                tasks_created = workflow_data.get("tasks_created", [])

                logger.info(f"\n📋 Tasks Created ({len(tasks_created)}):\n")
                for task in tasks_created:
                    logger.info(
                        f"→ {task.get('task_type').upper()}: {task.get('description')}"
                    )
                    logger.info(f"  Assigned to: {task.get('staff_name', 'Pending')}")
                    logger.info(f"  Priority: {task.get('priority').upper()}")
                    logger.info(f"  Reasoning: {task.get('reasoning', 'N/A')}")
                    logger.info("")

                logger.info("OK All tasks assigned successfully")

            # Final summary
            logger.info("\n" + "=" * 60)
            logger.info("OK PATIENT ADMISSION COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Patient: {patient.get('name')}")
            logger.info(f"Assigned Bed: {bed_number}")
            logger.info(f"Tasks Created: {len(tasks_created)}")
            logger.info("=" * 60 + "\n")

            return {
                "success": True,
                "patient_id": patient_id,
                "patient_name": patient.get("name"),
                "bed_id": bed_id,
                "bed_number": bed_number,
                "tasks_created": len(tasks_created),
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Error in patient admission workflow: {e}")
            return {"success": False, "message": str(e)}

    async def run_system_analysis(self):
        """Run system analysis using Memory Agent"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("RUNNING SYSTEM ANALYSIS")
            logger.info("=" * 60)

            # Get current state
            state_response = await self.memory_agent.process(
                {"type": "get_system_state"}
            )
            state = state_response.get("data", {})

            logger.info("\nCurrent Hospital State:\n")
            logger.info(f"Beds:")
            logger.info(f"  Total: {state.get('beds', {}).get('total', 0)}")
            logger.info(f"  Available: {state.get('beds', {}).get('available', 0)}")
            logger.info(f"  Occupied: {state.get('beds', {}).get('occupied', 0)}")
            logger.info(f"  Cleaning: {state.get('beds', {}).get('cleaning', 0)}")

            logger.info(f"\nPatients:")
            logger.info(f"  Total: {state.get('patients', {}).get('total', 0)}")
            logger.info(f"  Waiting: {state.get('patients', {}).get('waiting', 0)}")
            logger.info(f"  Admitted: {state.get('patients', {}).get('admitted', 0)}")

            logger.info(f"\nStaff:")
            logger.info(f"  On Shift: {state.get('staff', {}).get('on_shift', 0)}")
            logger.info(f"  Nurses: {state.get('staff', {}).get('nurses', 0)}")
            logger.info(f"  Cleaners: {state.get('staff', {}).get('cleaners', 0)}")

            logger.info(f"\nTasks:")
            logger.info(f"  Active: {state.get('tasks', {}).get('total', 0)}")
            logger.info(f"  Pending: {state.get('tasks', {}).get('pending', 0)}")
            logger.info(
                f"  In Progress: {state.get('tasks', {}).get('in_progress', 0)}"
            )

            # Run AI analysis
            logger.info("\nRunning AI-Powered State Analysis...\n")
            analysis_response = await self.memory_agent.process(
                {"type": "analyze_state"}
            )
            analysis = analysis_response.get("data", {})

            # Display critical alerts
            alerts = analysis.get("critical_alerts", [])
            if alerts:
                logger.info("CRITICAL ALERTS:")
                for alert in alerts:
                    logger.info(
                        f"  [{alert.get('severity', 'unknown').upper()}] {alert.get('message', '')}"
                    )
                    logger.info(
                        f"    Action Needed: {alert.get('action_needed', 'N/A')}\n"
                    )

            # Display bottlenecks
            bottlenecks = analysis.get("bottlenecks", [])
            if bottlenecks:
                logger.info("\nBOTTLENECKS DETECTED:")
                for bottleneck in bottlenecks:
                    logger.info(
                        f"  {bottleneck.get('area', 'unknown')}: {bottleneck.get('description', '')}"
                    )
                    logger.info(
                        f"    Recommendation: {bottleneck.get('recommendation', 'N/A')}\n"
                    )

            # Display recommendations
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                logger.info("\nRECOMMENDATIONS:")
                for rec in recommendations:
                    logger.info(f"  • {rec}")

            logger.info("\n" + "=" * 60 + "\n")

        except Exception as e:
            logger.error(f"Error running system analysis: {e}")

    async def demo_scenario(self):
        """Run a demo scenario"""
        logger.info("\n" + "=" * 60)
        logger.info("RUNNING DEMO SCENARIO")
        logger.info("=" * 60 + "\n")

        # Note: Staff is 0 because we created users, not staff
        # Users and staff are separate in the new schema

        # First, run system analysis
        await self.run_system_analysis()

        # Note: To run patient admission, you need to have a patient in Firebase
        # Uncomment and modify the line below with an actual patient ID
        # await self.handle_new_patient_admission("patient_id_here")

        logger.info("Demo scenario complete!\n")


async def main():
    """Main entry point"""
    setup_logging()

    try:
        # Initialize agent system
        system = CareFlowAgentSystem()
        await system.initialize()

        # Run demo scenario
        await system.demo_scenario()

        # Keep system running (in production, this would be a server)
        logger.info("Agent system is ready. Press Ctrl+C to exit.\n")

        # For now, just exit after demo
        # In production, you would keep this running to handle requests

    except KeyboardInterrupt:
        logger.info("\nShutting down agent system...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
