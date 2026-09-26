import csv
from pathlib import Path
from typing import Any, Dict, List

from .storage import add_candidate, add_target, create_project


DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def load_demo_project() -> int:
    target_structure = (DEMO_DIR / "toy_target.pdb").read_text()
    project_id = create_project({
        "name": "Illustrative GPCR binder triage",
        "description": "Synthetic end-to-end demo for the ProteinDesign Insight workflow.",
        "target": "Synthetic GPCR-like target fixture",
        "identifier": "DEMO-SYNTHETIC-GPCR",
        "design_method": "Illustrative de novo generation",
        "objective": "Prioritize candidates for follow-up experiments",
        "notes": "Demo only. All structures and experimental values are illustrative test fixtures, not biological evidence.",
        "is_demo": True,
    })
    add_target(project_id, {
        "name": "Primary target · active fixture",
        "identifier": "SYNTHETIC_ACTIVE",
        "structure_text": target_structure,
        "structure_format": "pdb",
        "state": "active",
    })
    add_target(project_id, {
        "name": "Primary target · inactive fixture",
        "identifier": "SYNTHETIC_INACTIVE",
        "structure_text": "",
        "structure_format": "pdb",
        "state": "inactive",
    })
    add_target(project_id, {
        "name": "Related off-target fixture",
        "identifier": "SYNTHETIC_OFF_TARGET",
        "structure_text": target_structure,
        "structure_format": "pdb",
        "state": "off-target",
        "is_off_target": True,
    })
    structure_by_candidate = {
        "PD-001": (DEMO_DIR / "toy_candidate_001.pdb").read_text(),
        "PD-002": (DEMO_DIR / "toy_candidate_002.pdb").read_text(),
    }
    with (DEMO_DIR / "candidates.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            add_candidate(project_id, {
                **row,
                "structure_text": structure_by_candidate.get(row["candidate_id"], ""),
                "metadata": {"demo_label": "Illustrative synthetic test data"},
            })
    return project_id
