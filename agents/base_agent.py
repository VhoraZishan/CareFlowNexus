"""
Base Agent Class for CareFlow Nexus
Provides common functionality for all AI agents
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.firebase_service import FirebaseService
from services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in CareFlow Nexus

    Provides common functionality:
    - Logging and decision tracking
    - Input validation
    - Error handling
    - Response formatting
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        firebase_service: FirebaseService,
        gemini_service: GeminiService,
    ):
        """
        Initialize base agent

        Args:
            agent_id: Unique identifier for this agent instance
            agent_type: Type of agent (state_manager, bed_allocator, task_coordinator)
            firebase_service: Firebase service instance
            gemini_service: Gemini AI service instance
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.firebase = firebase_service
        self.gemini = gemini_service
        self.logger = logging.getLogger(f"agent.{agent_type}")

        self.logger.info(f"Initialized {agent_type} agent with ID: {agent_id}")

    @abstractmethod
    async def process(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - must be implemented by subclasses

        Args:
            request_data: Input request data

        Returns:
            Response dictionary
        """
        pass

    def validate_input(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate input data has required fields

        Args:
            data: Input data dictionary
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, missing_fields)
        """
        if not isinstance(data, dict):
            return False, required_fields

        missing = [field for field in required_fields if field not in data]

        if missing:
            self.logger.warning(f"Missing required fields: {missing}")

        return len(missing) == 0, missing

    async def log_decision(
        self,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log agent decision to Firebase event logs

        Args:
            action: Action taken by agent
            input_data: Input data that led to decision
            output_data: Output/result of decision
            reasoning: Optional reasoning explanation
            metadata: Optional additional metadata
        """
        try:
            event_data = {
                "entity_type": "agent_decision",
                "entity_id": self.agent_id,
                "action": action,
                "triggered_by": self.agent_type,
                "details": {
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type,
                    "action": action,
                    "input": input_data,
                    "output": output_data,
                    "reasoning": reasoning,
                    "metadata": metadata or {},
                    "timestamp": datetime.now().isoformat(),
                },
            }

            await self.firebase.log_event(event_data)
            self.logger.info(f"Logged decision: {action}")

        except Exception as e:
            self.logger.error(f"Failed to log decision: {e}")

    async def log_error(
        self,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
        error_type: str = "general",
    ) -> None:
        """
        Log error event

        Args:
            error_message: Error message
            context: Optional context information
            error_type: Type of error
        """
        try:
            event_data = {
                "entity_type": "agent_error",
                "entity_id": self.agent_id,
                "action": f"error_{error_type}",
                "triggered_by": self.agent_type,
                "details": {
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type,
                    "error_type": error_type,
                    "error_message": error_message,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat(),
                },
            }

            await self.firebase.log_event(event_data)
            self.logger.error(f"Error logged: {error_message}")

        except Exception as e:
            self.logger.error(f"Failed to log error: {e}")

    def format_response(
        self,
        success: bool,
        data: Any = None,
        message: str = "",
        error_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Format standardized response

        Args:
            success: Whether operation was successful
            data: Response data
            message: Response message
            error_type: Optional error type if not successful

        Returns:
            Formatted response dictionary
        """
        response = {
            "success": success,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data,
        }

        if not success:
            response["error"] = True
            response["error_type"] = error_type or "unknown"

        return response

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit event for other agents or systems

        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            event_data = {
                "entity_type": event_type,
                "entity_id": self.agent_id,
                "action": f"emit_{event_type}",
                "triggered_by": self.agent_type,
                "details": data,
            }

            await self.firebase.log_event(event_data)
            self.logger.debug(f"Emitted event: {event_type}")

        except Exception as e:
            self.logger.error(f"Failed to emit event: {e}")

    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Safely get value from dictionary with default

        Args:
            data: Dictionary to get from
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value or default
        """
        return data.get(key, default) if isinstance(data, dict) else default

    def _validate_score(self, score: Any, min_val: int = 0, max_val: int = 100) -> int:
        """
        Validate and normalize score to range

        Args:
            score: Score value
            min_val: Minimum valid score
            max_val: Maximum valid score

        Returns:
            Validated score
        """
        try:
            score_int = int(float(score))
            return max(min_val, min(max_val, score_int))
        except (ValueError, TypeError):
            return 0

    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent information

        Returns:
            Agent info dictionary
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": "active",
            "capabilities": self.get_capabilities(),
        }

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities - must be implemented by subclasses

        Returns:
            List of capability strings
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} type={self.agent_type}>"

    def __str__(self) -> str:
        return f"{self.agent_type.title()} Agent ({self.agent_id})"
