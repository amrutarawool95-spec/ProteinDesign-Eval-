"""Transparent multi-objective ranking; scores never imply experimental success."""
from typing import Any

DEFAULT_WEIGHTS = {
    "structure": 0.20, "interface": 0.20, "specificity": 0.15,
    "conformation": 0.15, "diversity": 0.15, "uncertainty": 0.10, "feasibility": 0.05,
}

def validate_weights(weights: dict[str, float]) -> None:
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("ranking weights must sum to 1.0")
    if any(value < 0 for value in weights.values()):
        raise ValueError("ranking weights cannot be negative")

def rank_candidate(features: dict[str, float], weights: dict[str, float] | None = None) -> dict[str, Any]:
    active = weights or DEFAULT_WEIGHTS
    validate_weights(active)
    available = {key: features[key] for key in active if key in features and features[key] is not None}
    if not available:
        return {"score": None, "label": "Unavailable", "breakdown": {}}
    score = sum(available[key] * active[key] for key in available) / sum(active[key] for key in available)
    return {"score": round(score, 4), "label": "Calculated", "breakdown": {key: features[key] * active[key] for key in available}}