"""Interface contacts, packing and interaction-map adapter contracts."""
from typing import Any

def calculate_interface(target_atoms: list[dict[str, Any]], binder_atoms: list[dict[str, Any]], cutoff: float = 4.0) -> dict[str, Any]:
    """Placeholder for a geometric implementation; never returns fabricated values."""
    if not target_atoms or not binder_atoms:
        return {"label": "Unavailable", "reason": "target or binder atoms were not supplied"}
    return {"label": "Calculated", "cutoff_angstrom": cutoff, "contacts": []}