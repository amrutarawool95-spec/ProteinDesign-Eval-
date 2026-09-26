from dataclasses import dataclass, field
from typing import Literal

EvidenceLabel = Literal["Calculated", "Model-derived", "Experimental", "Unavailable"]

@dataclass
class Evidence:
    value: float | str | None
    label: EvidenceLabel
    method: str
    version: str | None = None
    uncertainty: float | None = None

@dataclass
class CandidateFeatures:
    candidate_id: str
    sequence: dict[str, Evidence] = field(default_factory=dict)
    structure: dict[str, Evidence] = field(default_factory=dict)
    interface: dict[str, Evidence] = field(default_factory=dict)
    specificity: dict[str, Evidence] = field(default_factory=dict)
    conformation: dict[str, Evidence] = field(default_factory=dict)
    diversity: dict[str, Evidence] = field(default_factory=dict)
    feasibility: dict[str, Evidence] = field(default_factory=dict)