"""
Configuration for CareFlow Nexus AI Agents
Loads environment variables and provides centralized config
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class FirebaseConfig:
    """Firebase configuration"""

    service_account_path: str
    database_url: Optional[str] = None

    @classmethod
    def from_env(cls):
        return cls(
            service_account_path=os.getenv(
                "FIREBASE_SERVICE_ACCOUNT_PATH", "./config/serviceAccountKey.json"
            ),
            database_url=os.getenv("FIREBASE_DATABASE_URL"),
        )


@dataclass
class GeminiConfig:
    """Gemini AI configuration"""

    api_key: str
    model_name: str = "gemini-2.0-flash-exp"
    temperature: float = 0.5
    max_tokens: int = 2048

    @classmethod
    def from_env(cls):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        return cls(
            api_key=api_key,
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.5")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "2048")),
        )


@dataclass
class AgentConfig:
    """Agent-specific configuration"""

    # Memory Agent (State Manager)
    state_refresh_interval: int = 300  # 5 minutes

    # Bed Allocator Agent
    rule_weight: float = 0.5  # 50% rule-based, 50% AI
    ai_weight: float = 0.5
    allocation_confidence_threshold: int = 70

    # Task Coordinator Agent
    max_staff_workload: int = 5
    task_check_interval: int = 60  # 1 minute
    task_timeout_warning: int = 1800  # 30 minutes
    task_timeout_critical: int = 3600  # 1 hour

    @classmethod
    def from_env(cls):
        return cls(
            state_refresh_interval=int(os.getenv("AGENT_REFRESH_INTERVAL", "300")),
            rule_weight=float(os.getenv("RULE_WEIGHT", "0.5")),
            ai_weight=float(os.getenv("AI_WEIGHT", "0.5")),
            allocation_confidence_threshold=int(
                os.getenv("ALLOCATION_CONFIDENCE_THRESHOLD", "70")
            ),
            max_staff_workload=int(os.getenv("MAX_STAFF_WORKLOAD", "5")),
            task_check_interval=int(os.getenv("TASK_CHECK_INTERVAL", "60")),
            task_timeout_warning=int(os.getenv("TASK_TIMEOUT_WARNING", "1800")),
            task_timeout_critical=int(os.getenv("TASK_TIMEOUT_CRITICAL", "3600")),
        )


@dataclass
class SystemConfig:
    """System-wide configuration"""

    environment: str
    log_level: str
    debug: bool

    @classmethod
    def from_env(cls):
        env = os.getenv("ENVIRONMENT", "development")
        return cls(
            environment=env,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            debug=env == "development",
        )


class Config:
    """Main configuration class"""

    def __init__(self):
        self.firebase = FirebaseConfig.from_env()
        self.gemini = GeminiConfig.from_env()
        self.agent = AgentConfig.from_env()
        self.system = SystemConfig.from_env()

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check Firebase
        if not os.path.exists(self.firebase.service_account_path):
            errors.append(
                f"Firebase service account file not found: {self.firebase.service_account_path}"
            )

        # Check Gemini
        if not self.gemini.api_key:
            errors.append("GOOGLE_API_KEY not set")

        # Check weights sum to 1.0
        if abs(self.agent.rule_weight + self.agent.ai_weight - 1.0) > 0.01:
            errors.append(
                f"Rule weight ({self.agent.rule_weight}) and AI weight ({self.agent.ai_weight}) must sum to 1.0"
            )

        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False

        return True

    def __repr__(self):
        return (
            f"Config(\n"
            f"  Environment: {self.system.environment}\n"
            f"  Log Level: {self.system.log_level}\n"
            f"  Gemini Model: {self.gemini.model_name}\n"
            f"  Agent Weights: Rule={self.agent.rule_weight}, AI={self.agent.ai_weight}\n"
            f")"
        )


# Global config instance
config = Config()
