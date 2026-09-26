from typing import Any, Dict, Iterable, List

from .interface import interface_metrics


def compare_specificity(candidate: Dict[str, Any], primary_target: Dict[str, Any], off_targets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    primary = interface_metrics(primary_target.get("structure_text", ""), candidate.get("structure_text", ""), primary_target.get("structure_format", ""), candidate.get("structure_format", ""))
    comparisons = []
    for target in off_targets:
        result = interface_metrics(target.get("structure_text", ""), candidate.get("structure_text", ""), target.get("structure_format", ""), candidate.get("structure_format", ""))
        comparisons.append({"target": target.get("name") or target.get("identifier") or "Off-target", "is_off_target": True, **result})
    if not primary.get("available"):
        return {"available": False, "primary": primary, "off_targets": comparisons, "interpretation": "Insufficient structure data for computational specificity comparison."}
    values = [row.get("contacts") or 0 for row in comparisons if row.get("available")]
    primary_contacts = primary.get("contacts") or 0
    max_off = max(values) if values else None
    compatibility = round(primary_contacts / max(primary_contacts + (max_off or 0), 1), 3) if max_off is not None else None
    return {
        "available": True,
        "primary": primary,
        "off_targets": comparisons,
        "primary_contacts": primary_contacts,
        "max_off_target_contacts": max_off,
        "contact_based_compatibility": compatibility,
        "risk": "Potential computational cross-reactivity" if max_off is not None and max_off >= primary_contacts * 0.7 else "No high contact-count off-target signal in supplied structures" if max_off is not None else "Off-target structures unavailable",
        "interpretation": "This is a calculated comparison, not evidence of biological specificity.",
    }
