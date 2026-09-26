"""Experimental outcome joins and association-only failure summaries."""
from collections import Counter
from typing import Any

def summarize_outcomes(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(record.get("binding_result", "Unavailable") for record in records)
    return {"label": "Experimental", "counts": dict(counts), "n": len(records)}