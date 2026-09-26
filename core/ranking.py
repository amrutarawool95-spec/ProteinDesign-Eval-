from typing import Any, Dict, Iterable, List, Optional


DEFAULT_WEIGHTS = {
    "structure_quality": 0.20,
    "interface_quality": 0.25,
    "specificity": 0.15,
    "conformational_robustness": 0.10,
    "diversity": 0.10,
    "uncertainty": 0.10,
    "sequence_quality": 0.10,
}


def _bounded(value: Optional[float], invert: bool = False) -> Optional[float]:
    if value is None:
        return None
    score = max(0.0, min(1.0, float(value)))
    return 1.0 - score if invert else score


def score_candidate(bundle: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    weights = weights or DEFAULT_WEIGHTS
    sequence = bundle.get("sequence", {})
    structure = bundle.get("structure", {})
    interface = bundle.get("interface", {})
    specificity = bundle.get("specificity", {})
    conformation = bundle.get("conformation", {})
    diversity = bundle.get("diversity", {})
    metric_map = {
        "structure_quality": _bounded(1.0 - min(1.0, (structure.get("clash_count") or 0) / 10)) if structure.get("available") else None,
        "interface_quality": _bounded(min(1.0, (interface.get("contacts") or 0) / 20)) if interface.get("available") else None,
        "specificity": specificity.get("contact_based_compatibility") if specificity.get("available") else None,
        "conformational_robustness": 1.0 if conformation.get("classification") == "Computationally state compatible" else 0.6 if conformation.get("available") else None,
        "diversity": 1.0 / max(1, len(diversity.get("cluster_sizes", {}))) if diversity.get("cluster_sizes") else None,
        "uncertainty": _bounded((structure.get("bfactor_mean") or 100) / 100, invert=True) if structure.get("bfactor_mean") is not None else None,
        "sequence_quality": _bounded(1.0 - ((sequence.get("hydrophobic_fraction") or 0) - 0.55) if sequence.get("hydrophobic_fraction") is not None else None),
    }
    available_weight = sum(weights.get(key, 0) for key, value in metric_map.items() if value is not None)
    contribution = {}
    for key, value in metric_map.items():
        contribution[key] = round(value * weights.get(key, 0), 4) if value is not None else None
    score = round(sum(value for value in contribution.values() if value is not None) / available_weight * 100, 2) if available_weight else None
    risks = []
    if structure.get("clash_count", 0) and structure["clash_count"] > 0:
        risks.append("Coordinate clashes detected")
    if not interface.get("available"):
        risks.append("Interface geometry unavailable")
    if not specificity.get("available"):
        risks.append("Specificity comparison unavailable")
    if structure.get("missing_residue_estimate"):
        risks.append("Possible missing residues")
    if sequence.get("unusual_composition"):
        risks.append("Unusual composition")
    return {"score": score, "components": metric_map, "contributions": contribution, "available_weight": round(available_weight, 4), "weights": weights, "risks": risks, "meaning": "Priority for experimental testing only; not a binding guarantee."}


def rank_bundles(bundles: Iterable[Dict[str, Any]], weights: Optional[Dict[str, float]] = None, constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    constraints = constraints or {}
    scored = []
    for bundle in bundles:
        result = score_candidate(bundle, weights)
        candidate_id = bundle.get("candidate_id", "")
        eligible = True
        if constraints.get("max_length") and bundle.get("sequence", {}).get("length", 0) > constraints["max_length"]:
            eligible = False
        if constraints.get("exclude_clashes") and bundle.get("structure", {}).get("clash_count", 0) > 0:
            eligible = False
        scored.append({"candidate_id": candidate_id, **result, "eligible": eligible})
    return sorted(scored, key=lambda row: (row["eligible"], row["score"] is not None, row["score"] or -1), reverse=True)


def pareto_front(rows: List[Dict[str, Any]], dimensions: Optional[List[str]] = None) -> List[str]:
    dimensions = dimensions or ["interface_quality", "structure_quality"]
    front = []
    for row in rows:
        current = row.get("components", {})
        dominated = False
        for other in rows:
            if other is row:
                continue
            other_values = other.get("components", {})
            if all((other_values.get(d) or 0) >= (current.get(d) or 0) for d in dimensions) and any((other_values.get(d) or 0) > (current.get(d) or 0) for d in dimensions):
                dominated = True
                break
        if not dominated:
            front.append(row.get("candidate_id", ""))
    return front
