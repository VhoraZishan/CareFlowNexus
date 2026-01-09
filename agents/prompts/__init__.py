"""
Prompts module for CareFlow Nexus AI Agents
Contains all prompt templates for Gemini AI interactions
"""

from .prompt_templates import (
    BedAllocatorPrompts,
    CommonPrompts,
    StateManagerPrompts,
    TaskCoordinatorPrompts,
)

__all__ = [
    "StateManagerPrompts",
    "BedAllocatorPrompts",
    "TaskCoordinatorPrompts",
    "CommonPrompts",
]
