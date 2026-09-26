from typing import Any, Dict, Iterable, List, Tuple

from .sequence import cluster_sequences, pairwise_identity


def diversity_analysis(candidates: Iterable[Dict[str, Any]], identity_threshold: float = 0.7) -> Dict[str, Any]:
    rows = list(candidates)
    assignments = cluster_sequences([(r.get("candidate_id", ""), r.get("sequence", "")) for r in rows], identity_threshold)
    pairwise = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            pairwise.append({"candidate_a": a.get("candidate_id"), "candidate_b": b.get("candidate_id"), "identity": round(pairwise_identity(a.get("sequence", ""), b.get("sequence", "")), 4)})
    cluster_sizes: Dict[int, int] = {}
    for cluster_id in assignments.values():
        cluster_sizes[cluster_id] = cluster_sizes.get(cluster_id, 0) + 1
    selected = []
    for cluster_id in sorted(cluster_sizes):
        member_ids = [cid for cid, cluster in assignments.items() if cluster == cluster_id]
        selected.append(member_ids[0])
    return {"threshold": identity_threshold, "assignments": assignments, "cluster_sizes": cluster_sizes, "pairwise_identity": pairwise, "diverse_selection": selected, "redundancy_count": max(0, len(rows) - len(selected))}
