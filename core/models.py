from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CandidateRecord:
    candidate_id: str
    sequence: str
    design_method: str = "Unknown"
    generation_round: str = ""
    structure_text: str = ""
    structure_format: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationIssue:
    level: str
    message: str
    record_id: Optional[str] = None


@dataclass
class AnalysisBundle:
    candidate_id: str
    sequence: Dict[str, Any] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)
    interface: Dict[str, Any] = field(default_factory=dict)
    specificity: Dict[str, Any] = field(default_factory=dict)
    conformation: Dict[str, Any] = field(default_factory=dict)
    uncertainty: Dict[str, Any] = field(default_factory=dict)
    diversity: Dict[str, Any] = field(default_factory=dict)
    ranking: Dict[str, Any] = field(default_factory=dict)
