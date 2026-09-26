"""Primary/off-target comparison with explicit unavailable states."""
from typing import Any

def compare_targets(primary: dict[str, Any], off_targets: list[dict[str, Any]]) -> dict[str, Any]:
    if not primary or not off_targets:
        return {"label": "Unavailable", "reason": "primary and off-target structures are required"}
    return {"label": "Calculated", "comparisons": [{"target_id": x.get("id"), "status": "pending"} for x in off_targets]}