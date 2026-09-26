import math
from typing import Any, Dict, List


def interface_metrics(target_text: str, candidate_text: str, target_fmt: str = "", candidate_fmt: str = "", cutoff: float = 5.0) -> Dict[str, Any]:
    from .structure import parse_structure
    target_atoms, target_errors = parse_structure(target_text, target_fmt)
    candidate_atoms, candidate_errors = parse_structure(candidate_text, candidate_fmt)
    if not target_atoms or not candidate_atoms:
        return {
            "available": False,
            "reason": "Both target and candidate structures are required for geometric interface metrics.",
            "contacts": None, "hydrogen_bonds": None, "salt_bridges": None, "hydrophobic_contacts": None,
            "interface_area": None, "packing": None, "errors": target_errors + candidate_errors,
        }
    contacts = []
    seen_pairs = set()
    for t in target_atoms:
        for c in candidate_atoms:
            distance = math.dist((t["x"], t["y"], t["z"]), (c["x"], c["y"], c["z"]))
            if distance <= cutoff:
                key = ((t["chain"], t["residue_number"]), (c["chain"], c["residue_number"]))
                if key not in seen_pairs:
                    contacts.append({
                        "target_chain": t["chain"], "target_residue": t["residue_number"], "target_name": t["residue"],
                        "candidate_chain": c["chain"], "candidate_residue": c["residue_number"], "candidate_name": c["residue"],
                        "distance": round(distance, 3),
                    })
                    seen_pairs.add(key)
    hbond_atoms = {"N", "O", "S"}
    salt_target = {"ASP", "GLU", "LYS", "ARG", "HIS"}
    hbond = sum(1 for row in contacts if row["target_name"] in salt_target and row["candidate_name"] in salt_target and row["distance"] <= 3.5)
    salt = sum(1 for row in contacts if row["target_name"] in {"ASP", "GLU"} and row["candidate_name"] in {"LYS", "ARG"} and row["distance"] <= 4.0)
    hydrophobic = sum(1 for row in contacts if row["target_name"] in set("AVILMFWY") and row["candidate_name"] in set("AVILMFWY"))
    unique_target = len({(row["target_chain"], row["target_residue"]) for row in contacts})
    unique_candidate = len({(row["candidate_chain"], row["candidate_residue"]) for row in contacts})
    return {
        "available": True,
        "contacts": len(contacts),
        "contacting_residues": contacts[:250],
        "hydrogen_bonds": hbond,
        "salt_bridges": salt,
        "hydrophobic_contacts": hydrophobic,
        "interface_area": round(float(unique_target + unique_candidate) * 6.2, 2),
        "packing": round(min(1.0, len(contacts) / max(unique_target + unique_candidate, 1) / 4), 3),
        "confidence": "Calculated geometric heuristic; no experimental confidence assigned.",
        "errors": target_errors + candidate_errors,
    }
