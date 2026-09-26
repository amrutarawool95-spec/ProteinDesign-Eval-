"""Sequence QC and feature extraction. No metric is imputed when input is absent."""
from collections import Counter
from math import log

HYDROPHOBIC = set("AILMFWVY")
CHARGED = set("DEKR")

def validate_sequence(sequence: str) -> list[str]:
    errors: list[str] = []
    clean = sequence.replace(" ", "").replace("\n", "").upper()
    if not clean:
        errors.append("sequence is empty")
    if any(aa not in "ACDEFGHIKLMNPQRSTVWY" for aa in clean):
        errors.append("sequence contains non-standard amino acids")
    return errors

def sequence_features(sequence: str) -> dict[str, float | int]:
    clean = sequence.replace(" ", "").replace("\n", "").upper()
    errors = validate_sequence(clean)
    if errors:
        raise ValueError("; ".join(errors))
    composition = Counter(clean)
    length = len(clean)
    entropy = -sum((n / length) * log(n / length, 2) for n in composition.values())
    return {
        "length": length,
        "hydrophobic_fraction": sum(composition[a] for a in HYDROPHOBIC) / length,
        "charged_fraction": sum(composition[a] for a in CHARGED) / length,
        "composition_entropy": entropy,
    }