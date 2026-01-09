"""
Utility functions for serializing Firestore data
"""

from datetime import datetime
from typing import Any


def serialize_firestore_data(data: Any) -> Any:
    """
    Recursively convert Firestore DatetimeWithNanoseconds to ISO format strings
    and handle other non-JSON-serializable types

    Args:
        data: Any data structure that might contain Firestore types

    Returns:
        JSON-serializable version of the data
    """
    if data is None:
        return None

    # Handle datetime objects (including DatetimeWithNanoseconds)
    if hasattr(data, "isoformat"):
        return data.isoformat()

    # Handle dictionaries
    if isinstance(data, dict):
        return {key: serialize_firestore_data(value) for key, value in data.items()}

    # Handle lists
    if isinstance(data, list):
        return [serialize_firestore_data(item) for item in data]

    # Handle tuples
    if isinstance(data, tuple):
        return tuple(serialize_firestore_data(item) for item in data)

    # Return as-is for primitive types (str, int, float, bool, etc.)
    return data
