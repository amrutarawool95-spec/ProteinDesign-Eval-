import math
import re
from typing import Any, Dict, List, Tuple

import numpy as np


def _float(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_pdb(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    atoms: List[Dict[str, Any]] = []
    errors: List[str] = []
    for line_number, line in enumerate((text or "").splitlines(), 1):
        if not line.startswith(("ATOM", "HETATM")):
            continue
        try:
            atom = {
                "record": line[0:6].strip(),
                "atom": line[12:16].strip(),
                "residue": line[17:20].strip(),
                "chain": (line[21:22].strip() or "_"),
                "residue_number": int(line[22:26].strip()),
                "x": float(line[30:38].strip()),
                "y": float(line[38:46].strip()),
                "z": float(line[46:54].strip()),
                "occupancy": _float(line[54:60].strip()),
                "bfactor": _float(line[60:66].strip()),
                "element": (line[76:78].strip() or line[12:16].strip()[0:1]).upper(),
            }
            atoms.append(atom)
        except (ValueError, IndexError):
            errors.append(f"Malformed PDB atom record on line {line_number}.")
    return atoms, errors


def parse_mmcif(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    # Lightweight parser for common whitespace-delimited atom_site loops.
    lines = [line.strip() for line in (text or "").splitlines() if line.strip() and not line.strip().startswith("#")]
    headers = []
    start = None
    for i, line in enumerate(lines):
        if line.startswith("_atom_site."):
            headers.append(line.split()[0].replace("_atom_site.", ""))
            start = i + 1
        elif headers and (line.startswith("ATOM") or line.startswith("HETATM")):
            break
    if not headers or start is None:
        return [], ["Could not find a readable _atom_site loop in the mmCIF text."]
    atoms = []
    errors = []
    for line in lines[start:]:
        if line.startswith(("loop_", "_")):
            break
        parts = line.split()
        if len(parts) < len(headers):
            continue
        row = dict(zip(headers, parts[:len(headers)]))
        try:
            atoms.append({
                "record": row.get("group_PDB", "ATOM"),
                "atom": row.get("label_atom_id", row.get("auth_atom_id", "")),
                "residue": row.get("label_comp_id", row.get("auth_comp_id", "")),
                "chain": row.get("label_asym_id", row.get("auth_asym_id", "_")),
                "residue_number": int(float(row.get("label_seq_id", row.get("auth_seq_id", "0")))),
                "x": float(row["Cartn_x"]), "y": float(row["Cartn_y"]), "z": float(row["Cartn_z"]),
                "occupancy": _float(row.get("occupancy")), "bfactor": _float(row.get("B_iso_or_equiv")),
                "element": row.get("type_symbol", ""),
            })
        except (ValueError, KeyError):
            errors.append("Skipped a malformed mmCIF atom row.")
    return atoms, errors


def parse_structure(text: str, fmt: str = "") -> Tuple[List[Dict[str, Any]], List[str]]:
    fmt = (fmt or "").lower()
    if fmt in {"cif", "mmcif"} or "_atom_site." in (text or ""):
        return parse_mmcif(text)
    return parse_pdb(text)


def structure_metrics(text: str, fmt: str = "", expected_sequence: str = "") -> Dict[str, Any]:
    atoms, errors = parse_structure(text, fmt)
    if not atoms:
        return {"available": False, "error": "; ".join(errors) if errors else "No atoms found.", "errors": errors}
    coords = np.array([[a["x"], a["y"], a["z"]] for a in atoms], dtype=float)
    center = coords.mean(axis=0)
    distances = np.sqrt(((coords - center) ** 2).sum(axis=1))
    residues = sorted({(a["chain"], a["residue_number"]) for a in atoms})
    b_factors = [a["bfactor"] for a in atoms if a["bfactor"] is not None]
    heavy = [a for a in atoms if a["element"] not in {"H", "D"}]
    clashes = 0
    for i, atom_a in enumerate(heavy):
        for atom_b in heavy[i + 1:]:
            if atom_a["chain"] == atom_b["chain"] and atom_a["residue_number"] == atom_b["residue_number"]:
                continue
            d = math.dist((atom_a["x"], atom_a["y"], atom_a["z"]), (atom_b["x"], atom_b["y"], atom_b["z"]))
            if d < 1.6:
                clashes += 1
    missing = None
    if expected_sequence:
        missing = max(0, len(expected_sequence) - len(residues))
    return {
        "available": True,
        "atom_count": len(atoms),
        "residue_count": len(residues),
        "chain_count": len({a["chain"] for a in atoms}),
        "compactness_radius": round(float(distances.mean()), 3),
        "radius_of_gyration": round(float(np.sqrt(((coords - center) ** 2).sum(axis=1).mean())), 3),
        "clash_count": clashes,
        "missing_residue_estimate": missing,
        "bfactor_mean": round(float(np.mean(b_factors)), 3) if b_factors else None,
        "bfactor_available": bool(b_factors),
        # A PDB B-factor is not a pLDDT value. Keep pLDDT unavailable unless a
        # model runner supplies it as metadata rather than silently relabeling it.
        "plddt": None,
        "pae": None,
        "secondary_structure": "Unavailable without annotated structure or secondary-structure assignment.",
        "errors": errors,
    }


def atom_table(text: str, fmt: str = "") -> List[Dict[str, Any]]:
    return parse_structure(text, fmt)[0]
