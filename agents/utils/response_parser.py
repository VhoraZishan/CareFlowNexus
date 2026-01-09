"""
Response Parser Utility for CareFlow Nexus
Handles parsing and validation of Gemini AI responses
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResponseParser:
    """Utility class for parsing and validating AI responses"""

    @staticmethod
    def extract_json(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text response (handles various formats)

        Args:
            text: Text containing JSON

        Returns:
            Parsed JSON dictionary or None
        """
        if not text:
            return None

        # Try direct JSON parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        patterns = [
            r"```json\s*(\{.*?\})\s*```",  # ```json {...} ```
            r"```\s*(\{.*?\})\s*```",  # ``` {...} ```
            r"```json\s*(\[.*?\])\s*```",  # ```json [...] ```
            r"```\s*(\[.*?\])\s*```",  # ``` [...] ```
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    continue

        # Try to find any JSON object or array in the text
        json_object_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        json_array_pattern = r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]"

        for pattern in [json_object_pattern, json_array_pattern]:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    # Verify it's a meaningful JSON (not just empty)
                    if parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue

        logger.warning("Could not extract valid JSON from response")
        return None

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate that dictionary contains required fields

        Args:
            data: Dictionary to validate
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, missing_fields)
        """
        if not isinstance(data, dict):
            return False, required_fields

        missing = [field for field in required_fields if field not in data]
        return len(missing) == 0, missing

    @staticmethod
    def sanitize_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean and normalize response data

        Args:
            data: Raw response data

        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key, value in data.items():
            # Clean key (remove special chars, lowercase)
            clean_key = key.strip().lower().replace(" ", "_")

            # Clean value based on type
            if isinstance(value, str):
                sanitized[clean_key] = value.strip()
            elif isinstance(value, dict):
                sanitized[clean_key] = ResponseParser.sanitize_response(value)
            elif isinstance(value, list):
                sanitized[clean_key] = [
                    ResponseParser.sanitize_response(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[clean_key] = value

        return sanitized

    @staticmethod
    def validate_score(score: Any, min_val: int = 0, max_val: int = 100) -> int:
        """
        Validate and normalize score to range

        Args:
            score: Score value (any type)
            min_val: Minimum valid score
            max_val: Maximum valid score

        Returns:
            Validated score within range
        """
        try:
            score_int = int(float(score))
            return max(min_val, min(max_val, score_int))
        except (ValueError, TypeError):
            logger.warning(f"Invalid score value: {score}, returning 0")
            return 0

    @staticmethod
    def parse_bed_allocation_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate bed allocation response

        Args:
            response: Raw response from AI

        Returns:
            Validated and structured response
        """
        try:
            recommendations = response.get("recommendations", [])
            if not isinstance(recommendations, list):
                recommendations = []

            parsed_recs = []
            for rec in recommendations[:3]:  # Top 3 only
                if not isinstance(rec, dict):
                    continue

                parsed_rec = {
                    "bed_id": rec.get("bed_id", ""),
                    "bed_number": rec.get("bed_number", ""),
                    "ward": rec.get("ward", ""),
                    "score": ResponseParser.validate_score(rec.get("score", 0)),
                    "reasoning": rec.get("reasoning", "No reasoning provided"),
                    "pros": rec.get("pros", [])
                    if isinstance(rec.get("pros"), list)
                    else [],
                    "cons": rec.get("cons", [])
                    if isinstance(rec.get("cons"), list)
                    else [],
                }

                parsed_recs.append(parsed_rec)

            return {
                "recommendations": parsed_recs,
                "overall_confidence": ResponseParser.validate_score(
                    response.get("overall_confidence", 50)
                ),
                "considerations": response.get("considerations", ""),
            }
        except Exception as e:
            logger.error(f"Error parsing bed allocation response: {e}")
            return {
                "recommendations": [],
                "overall_confidence": 0,
                "considerations": "",
            }

    @staticmethod
    def parse_requirement_extraction_response(
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Parse and validate requirement extraction response

        Args:
            response: Raw response from AI

        Returns:
            Validated requirements dictionary
        """
        try:
            return {
                "needs_oxygen": bool(response.get("needs_oxygen", False)),
                "needs_ventilator": bool(response.get("needs_ventilator", False)),
                "needs_cardiac_monitor": bool(
                    response.get("needs_cardiac_monitor", False)
                ),
                "needs_isolation": bool(response.get("needs_isolation", False)),
                "preferred_ward": response.get("preferred_ward"),
                "proximity_preference": ResponseParser.validate_score(
                    response.get("proximity_preference", 5), 1, 10
                ),
                "special_considerations": response.get("special_considerations", [])
                if isinstance(response.get("special_considerations"), list)
                else [],
                "confidence": ResponseParser.validate_score(
                    response.get("confidence", 50)
                ),
                "reasoning": response.get("reasoning", ""),
            }
        except Exception as e:
            logger.error(f"Error parsing requirement extraction response: {e}")
            return {
                "needs_oxygen": False,
                "needs_ventilator": False,
                "needs_cardiac_monitor": False,
                "needs_isolation": False,
                "preferred_ward": None,
                "proximity_preference": 5,
                "special_considerations": [],
                "confidence": 0,
                "reasoning": "Error parsing response",
            }

    @staticmethod
    def parse_staff_assignment_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate staff assignment response

        Args:
            response: Raw response from AI

        Returns:
            Validated assignment dictionary
        """
        try:
            alternatives = response.get("alternatives", [])
            if not isinstance(alternatives, list):
                alternatives = []

            return {
                "recommended_staff_id": response.get("recommended_staff_id", ""),
                "staff_name": response.get("staff_name", ""),
                "reasoning": response.get("reasoning", "No reasoning provided"),
                "workload_impact": response.get("workload_impact", ""),
                "concerns": response.get("concerns", [])
                if isinstance(response.get("concerns"), list)
                else [],
                "alternatives": alternatives[:2],  # Top 2 alternatives
                "confidence": ResponseParser.validate_score(
                    response.get("confidence", 50)
                ),
            }
        except Exception as e:
            logger.error(f"Error parsing staff assignment response: {e}")
            return {
                "recommended_staff_id": "",
                "staff_name": "",
                "reasoning": "Error parsing response",
                "workload_impact": "",
                "concerns": [],
                "alternatives": [],
                "confidence": 0,
            }

    @staticmethod
    def parse_state_analysis_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate state analysis response

        Args:
            response: Raw response from AI

        Returns:
            Validated analysis dictionary
        """
        try:
            return {
                "critical_alerts": response.get("critical_alerts", [])
                if isinstance(response.get("critical_alerts"), list)
                else [],
                "bottlenecks": response.get("bottlenecks", [])
                if isinstance(response.get("bottlenecks"), list)
                else [],
                "capacity_forecast": response.get("capacity_forecast", {})
                if isinstance(response.get("capacity_forecast"), dict)
                else {},
                "recommendations": response.get("recommendations", [])
                if isinstance(response.get("recommendations"), list)
                else [],
            }
        except Exception as e:
            logger.error(f"Error parsing state analysis response: {e}")
            return {
                "critical_alerts": [],
                "bottlenecks": [],
                "capacity_forecast": {},
                "recommendations": [],
            }

    @staticmethod
    def combine_scores(
        rule_score: float, ai_score: float, rule_weight: float = 0.5
    ) -> float:
        """
        Combine rule-based and AI scores with weights

        Args:
            rule_score: Rule-based score (0-100)
            ai_score: AI-generated score (0-100)
            rule_weight: Weight for rule score (0-1), AI gets (1-rule_weight)

        Returns:
            Combined score
        """
        ai_weight = 1.0 - rule_weight
        combined = (rule_score * rule_weight) + (ai_score * ai_weight)
        return round(combined, 2)

    @staticmethod
    def format_error_response(
        error_message: str, error_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Format error into standard response structure

        Args:
            error_message: Error message
            error_type: Type of error

        Returns:
            Error response dictionary
        """
        return {
            "success": False,
            "error": True,
            "error_type": error_type,
            "message": error_message,
            "data": None,
        }

    @staticmethod
    def format_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
        """
        Format success response

        Args:
            data: Response data
            message: Success message

        Returns:
            Success response dictionary
        """
        return {"success": True, "error": False, "message": message, "data": data}
