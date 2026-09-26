from typing import Any, Dict, Iterable, List


def normalize_feedback(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []
    for row in rows:
        normalized = {str(k).strip().lower().replace(" ", "_"): ("" if v is None else str(v).strip()) for k, v in row.items()}
        if normalized.get("candidate_id"):
            normalized["binding_result"] = normalized.get("binding_result", "")
            output.append(normalized)
    return output


def summarize_feedback(feedback: Iterable[Dict[str, Any]], analyses: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(feedback)
    analysis_map = {row.get("candidate_id"): row.get("payload", row) for row in analyses}
    successes, failures = [], []
    for row in rows:
        result = row.get("binding_result", "").lower()
        if result in {"yes", "positive", "success", "bound", "1", "true"}:
            successes.append(row)
        elif result in {"no", "negative", "failure", "failed", "0", "false"}:
            failures.append(row)
    failure_features = []
    for row in failures:
        payload = analysis_map.get(row.get("candidate_id"), {})
        sequence = payload.get("sequence", {})
        structure = payload.get("structure", {})
        failure_features.append({
            "candidate_id": row.get("candidate_id"),
            "observed_problem": row.get("notes") or "User-provided negative outcome",
            "hydrophobic_fraction": sequence.get("hydrophobic_fraction"),
            "charged_fraction": sequence.get("charged_fraction"),
            "clash_count": structure.get("clash_count"),
            "source": "Observed feedback plus calculated features; association only.",
        })
    return {
        "n_total": len(rows), "n_success": len(successes), "n_failure": len(failures),
        "unlabeled": max(0, len(rows) - len(successes) - len(failures)),
        "failure_features": failure_features,
        "can_model": len(successes) + len(failures) >= 10 and bool(successes) and bool(failures),
        "model_note": "Outcome modeling is withheld until at least 10 labeled records include both positive and negative examples." if not (len(successes) + len(failures) >= 10 and successes and failures) else "Enough labeled examples for a future, validated outcome model; no model is trained automatically.",
    }
