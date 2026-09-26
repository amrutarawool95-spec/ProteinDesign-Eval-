"""Compatibility across active/inactive/intermediate target states."""
from typing import Any

def classify_state_compatibility(states: list[dict[str, Any]]) -> dict[str, Any]:
    if len(states) < 2:
        return {"label": "Unavailable", "reason": "at least two target states are required"}
    return {"label": "Calculated", "classification": "unavailable_until_geometry_is_computed"}