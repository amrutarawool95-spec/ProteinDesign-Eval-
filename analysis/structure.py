"""Structure quality calculations. Adapters can wrap Biopython/MDAnalysis later."""
from typing import Any

def validate_structure(structure: dict[str, Any]) -> list[str]:
    errors = []
    if not structure.get("atoms"):
        errors.append("structure has no parsed atoms")
    if structure.get("missing_residues"):
        errors.append(f"missing residues: {structure['missing_residues']}")
    return errors

def structure_features(structure: dict[str, Any]) -> dict[str, Any]:
    """Return only values available in the input structure/model record."""
    values = {}
    for key in ("plddt", "pae", "secondary_structure", "compactness", "clashes"):
        if key in structure:
            values[key] = structure[key]
    return values