from typing import Any, Dict, Iterable, List

from .interface import interface_metrics


def compare_conformations(candidate: Dict[str, Any], states: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    for state in states:
        result = interface_metrics(state.get("structure_text", ""), candidate.get("structure_text", ""), state.get("structure_format", ""), candidate.get("structure_format", ""))
        rows.append({"state": state.get("state", state.get("name", "state")), **result})
    usable = [row for row in rows if row.get("available")]
    if len(usable) < 2:
        status = "Insufficient data"
        interpretation = "At least two target-state structures are needed for a computational state comparison."
    else:
        contact_values = [row.get("contacts") or 0 for row in usable]
        spread = max(contact_values) - min(contact_values)
        if spread <= max(2, 0.2 * max(contact_values)):
            status = "Computationally state compatible"
        elif min(contact_values) == 0:
            status = "Computationally state selective"
        else:
            status = "Conformationally sensitive"
        interpretation = "State label reflects supplied geometric comparisons only; it is not biological selectivity."
    return {"available": len(usable) >= 2, "states": rows, "classification": status, "interpretation": interpretation}
