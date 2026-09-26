from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from .validation import AA


def sequence_metrics(sequence: str) -> Dict[str, Any]:
    sequence = (sequence or "").upper()
    length = len(sequence)
    counts = Counter(sequence)
    hydrophobic = set("AVILMFWY")
    charged = set("DEKR")
    unusual = sorted(set(sequence) - AA)
    return {
        "length": length,
        "composition": {aa: counts.get(aa, 0) for aa in sorted(AA)},
        "hydrophobic_fraction": round(sum(counts[a] for a in hydrophobic) / length, 4) if length else None,
        "charged_fraction": round(sum(counts[a] for a in charged) / length, 4) if length else None,
        "unusual_residues": unusual,
        "unusual_composition": bool(length and (sum(counts[a] for a in hydrophobic) / length > 0.75 or sum(counts[a] for a in charged) / length > 0.45)),
        "proline_fraction": round(counts.get("P", 0) / length, 4) if length else None,
        "glycine_fraction": round(counts.get("G", 0) / length, 4) if length else None,
    }


def pairwise_identity(seq_a: str, seq_b: str) -> float:
    a, b = (seq_a or "").upper(), (seq_b or "").upper()
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    matches = sum(x == y for x, y in zip(a[:n], b[:n]))
    return matches / max(len(a), len(b))


def cluster_sequences(records: Iterable[Tuple[str, str]], threshold: float = 0.7) -> Dict[str, int]:
    representatives: List[str] = []
    assignments: Dict[str, int] = {}
    for cid, seq in records:
        assigned = None
        for cluster_id, rep in enumerate(representatives, 1):
            if pairwise_identity(seq, rep) >= threshold:
                assigned = cluster_id
                break
        if assigned is None:
            representatives.append(seq)
            assigned = len(representatives)
        assignments[cid] = assigned
    return assignments


def sequence_distance_matrix(records: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    rows = []
    for cid_a, seq_a in records:
        for cid_b, seq_b in records:
            if cid_a < cid_b:
                rows.append({"candidate_a": cid_a, "candidate_b": cid_b, "identity": round(pairwise_identity(seq_a, seq_b), 4)})
    return rows
