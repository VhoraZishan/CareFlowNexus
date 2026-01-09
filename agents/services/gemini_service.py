"""
Gemini Service for CareFlow Nexus
Handles all Gemini AI API interactions using gemini-2.0-flash-exp model
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class GeminiService:
    """Service class for Gemini AI API operations"""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini service

        Args:
            api_key: Google API key for Gemini
            model_name: Model name (default: gemini-2.0-flash-exp)
        """
        try:
            genai.configure(api_key=api_key)
            self.model_name = model_name
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini service initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_response(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048
    ) -> str:
        """
        Generate a text response from Gemini

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response
        """
        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                candidate_count=1,
            )

            response = self.model.generate_content(
                prompt, generation_config=generation_config
            )

            if response.text:
                logger.debug(f"Generated response: {response.text[:100]}...")
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return ""

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_json_response(
        self, prompt: str, temperature: float = 0.5, max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from Gemini

        Args:
            prompt: Input prompt (should instruct to return JSON)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dictionary
        """
        try:
            # Add JSON instruction to prompt if not present
            if "json" not in prompt.lower():
                prompt = f"{prompt}\n\nRespond ONLY with valid JSON."

            text_response = await self.generate_response(
                prompt, temperature=temperature, max_tokens=max_tokens
            )

            # Extract JSON from response
            json_data = self._extract_json(text_response)

            if json_data:
                logger.debug("Successfully extracted JSON from response")
                return json_data
            else:
                logger.warning("Failed to extract JSON, returning empty dict")
                return {}

        except Exception as e:
            logger.error(f"Error generating JSON response: {e}")
            return {}

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text response

        Args:
            text: Text containing JSON

        Returns:
            Parsed JSON dictionary or None
        """
        try:
            # Try direct JSON parse first
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.findall(json_pattern, text, re.DOTALL)

        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        logger.warning("Could not extract valid JSON from response")
        return None

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Generate structured response with system instruction

        Args:
            system_instruction: System-level instruction/context
            user_prompt: User query/request
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON response
        """
        try:
            # Create model with system instruction
            model_with_system = genai.GenerativeModel(
                self.model_name, system_instruction=system_instruction
            )

            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                candidate_count=1,
            )

            response = model_with_system.generate_content(
                user_prompt, generation_config=generation_config
            )

            if response.text:
                return self._extract_json(response.text) or {}
            return {}

        except Exception as e:
            logger.error(f"Error generating structured response: {e}")
            return {}

    async def analyze_text(
        self, text: str, analysis_type: str, context: Optional[Dict] = None
    ) -> str:
        """
        Analyze text with specific analysis type

        Args:
            text: Text to analyze
            analysis_type: Type of analysis (e.g., "diagnosis", "requirements", "sentiment")
            context: Optional additional context

        Returns:
            Analysis result as text
        """
        context_str = ""
        if context:
            context_str = f"\n\nContext: {json.dumps(context, indent=2)}"

        prompt = f"""
Analyze the following text for {analysis_type}:

{text}
{context_str}

Provide a clear, concise analysis.
"""

        return await self.generate_response(prompt, temperature=0.3)

    async def score_and_rank(
        self, items: List[Dict], criteria: str, context: Dict
    ) -> Dict[str, Any]:
        """
        Score and rank items based on criteria

        Args:
            items: List of items to rank
            criteria: Ranking criteria description
            context: Context information

        Returns:
            Dictionary with ranked items and scores
        """
        prompt = f"""
You are an expert ranking system.

CRITERIA: {criteria}

CONTEXT:
{json.dumps(context, indent=2)}

ITEMS TO RANK:
{json.dumps(items, indent=2)}

Score each item from 0-100 and rank them. Provide reasoning for each score.

Respond with JSON in this format:
{{
  "rankings": [
    {{
      "item_id": "id",
      "score": 0-100,
      "reasoning": "detailed explanation",
      "pros": ["advantage 1", "advantage 2"],
      "cons": ["concern 1", "concern 2"]
    }}
  ],
  "confidence": 0-100,
  "overall_recommendation": "summary"
}}
"""

        return await self.generate_json_response(prompt, temperature=0.5)

    async def extract_requirements(
        self, diagnosis: str, patient_info: Dict
    ) -> Dict[str, Any]:
        """
        Extract medical requirements from diagnosis

        Args:
            diagnosis: Patient diagnosis text
            patient_info: Patient information dictionary

        Returns:
            Dictionary of extracted requirements
        """
        prompt = f"""
You are a medical requirements analyzer.

PATIENT INFORMATION:
- Age: {patient_info.get("age", "Unknown")}
- Gender: {patient_info.get("gender", "Unknown")}
- Diagnosis: {diagnosis}
- Severity: {patient_info.get("severity", "moderate")}
- Mobility: {patient_info.get("mobility_status", "ambulatory")}

Extract the medical care requirements and respond with JSON:
{{
  "needs_oxygen": true/false,
  "needs_ventilator": true/false,
  "needs_cardiac_monitor": true/false,
  "needs_isolation": true/false,
  "preferred_ward": "ward name or null",
  "proximity_preference": 1-10,
  "special_considerations": ["list of special needs"],
  "reasoning": "brief explanation"
}}
"""

        return await self.generate_json_response(prompt, temperature=0.3)

    async def generate_task_assignment_reasoning(
        self, task: Dict, staff: Dict, context: Dict
    ) -> str:
        """
        Generate reasoning for task assignment

        Args:
            task: Task details
            staff: Staff member details
            context: Additional context

        Returns:
            Reasoning text
        """
        prompt = f"""
Explain why {staff.get("name")} is the best choice for this task:

TASK:
{json.dumps(task, indent=2)}

STAFF MEMBER:
{json.dumps(staff, indent=2)}

CONTEXT:
{json.dumps(context, indent=2)}

Provide a clear, concise explanation in 2-3 sentences.
"""

        return await self.generate_response(prompt, temperature=0.5)

    async def detect_bottlenecks(self, system_state: Dict) -> Dict[str, Any]:
        """
        Analyze system state for bottlenecks

        Args:
            system_state: Current system state metrics

        Returns:
            Bottleneck analysis
        """
        prompt = f"""
You are a hospital operations analyst.

CURRENT SYSTEM STATE:
{json.dumps(system_state, indent=2)}

Analyze for bottlenecks, inefficiencies, and potential issues.

Respond with JSON:
{{
  "bottlenecks": [
    {{
      "type": "bottleneck type",
      "severity": "low/medium/high/critical",
      "description": "what's wrong",
      "impact": "how it affects operations",
      "recommendation": "suggested action"
    }}
  ],
  "alerts": ["urgent issues requiring immediate attention"],
  "recommendations": ["proactive suggestions"],
  "capacity_forecast": "prediction for next 4-6 hours"
}}
"""

        return await self.generate_json_response(prompt, temperature=0.3)

    def validate_json_schema(self, data: Dict, required_keys: List[str]) -> bool:
        """
        Validate JSON data has required keys

        Args:
            data: JSON data to validate
            required_keys: List of required keys

        Returns:
            True if valid, False otherwise
        """
        return all(key in data for key in required_keys)

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "provider": "Google Gemini",
            "version": "2.0-flash-exp",
        }
