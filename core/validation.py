import csv
import io
import json
import re
from typing import Any, Dict, Iterable, List, Tuple

from .models import CandidateRecord, ValidationIssue

AA = set("ACDEFGHIKLMNPQRSTVWY")


def clean_sequence(raw: str) -> str:
    return re.sub(r"[^A-Za-z]", "", raw or "").upper()


def parse_fasta(text: str) -> Tuple[List[Tuple[str, str]], List[ValidationIssue]]:
    issues: List[ValidationIssue] = []
    records: List[Tuple[str, str]] = []
    if not text or not text.strip():
        return [], [ValidationIssue("error", "The FASTA file is empty.")]
    current_id = None
    chunks: List[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_id is not None:
                records.append((current_id, clean_sequence("".join(chunks))))
            current_id = line[1:].strip().split()[0]
            chunks = []
            if not current_id:
                issues.append(ValidationIssue("error", f"Missing FASTA identifier on line {line_number}."))
        elif current_id is None:
            issues.append(ValidationIssue("error", f"Sequence data appears before a FASTA header on line {line_number}."))
        else:
            invalid = set(line.upper()) - AA
            if invalid:
                issues.append(ValidationIssue("error", f"Invalid amino acid symbols {sorted(invalid)} on line {line_number}.", current_id))
            chunks.append(line)
    if current_id is not None:
        records.append((current_id, clean_sequence("".join(chunks))))
    if not records:
        issues.append(ValidationIssue("error", "No FASTA records were found."))
    seen = set()
    for record_id, sequence in records:
        if record_id in seen:
            issues.append(ValidationIssue("error", f"Duplicate candidate ID: {record_id}.", record_id))
        seen.add(record_id)
        if not sequence:
            issues.append(ValidationIssue("error", f"Candidate {record_id} has no residues.", record_id))
    return records, issues


def parse_candidate_csv(text: str) -> Tuple[List[CandidateRecord], List[ValidationIssue]]:
    issues: List[ValidationIssue] = []
    if not text or not text.strip():
        return [], [ValidationIssue("error", "The CSV file is empty.")]
    try:
        reader = csv.DictReader(io.StringIO(text))
        fields = {field.strip() for field in (reader.fieldnames or []) if field}
        required = {"candidate_id", "sequence"}
        missing = required - fields
        if missing:
            return [], [ValidationIssue("error", f"Missing required columns: {', '.join(sorted(missing))}.")]
        rows: List[CandidateRecord] = []
        seen = set()
        for line_number, row in enumerate(reader, 2):
            cid = (row.get("candidate_id") or "").strip()
            seq = clean_sequence(row.get("sequence") or "")
            if not cid:
                issues.append(ValidationIssue("error", f"Missing candidate_id on CSV row {line_number}."))
                continue
            if cid in seen:
                issues.append(ValidationIssue("error", f"Duplicate candidate ID: {cid}.", cid))
            seen.add(cid)
            invalid = set(seq) - AA
            if invalid:
                issues.append(ValidationIssue("error", f"Invalid amino acid symbols for {cid}: {sorted(invalid)}.", cid))
            if not seq:
                issues.append(ValidationIssue("error", f"Candidate {cid} has an empty sequence.", cid))
            rows.append(CandidateRecord(
                candidate_id=cid,
                sequence=seq,
                design_method=(row.get("design_method") or row.get("design method") or "Unknown").strip(),
                generation_round=(row.get("generation_round") or row.get("generation round") or "").strip(),
                structure_text=(row.get("structure") or "").strip(),
                structure_format=(row.get("structure_format") or "").strip(),
                metadata={k: v for k, v in row.items() if k not in {"candidate_id", "sequence", "design_method", "design method", "generation_round", "generation round", "structure", "structure_format"}},
            ))
        return rows, issues
    except csv.Error as exc:
        return [], [ValidationIssue("error", f"Malformed CSV: {exc}")]


def parse_candidate_json(text: str) -> Tuple[List[CandidateRecord], List[ValidationIssue]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return [], [ValidationIssue("error", f"Malformed JSON: {exc.msg}.")]
    rows = payload if isinstance(payload, list) else payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return [], [ValidationIssue("error", "JSON must be a list of candidates or an object with a candidates list.")]
    csv_text = io.StringIO()
    if not rows:
        return [], [ValidationIssue("error", "The JSON candidate list is empty.")]
    fieldnames = sorted({key for row in rows if isinstance(row, dict) for key in row.keys()} | {"candidate_id", "sequence"})
    writer = csv.DictWriter(csv_text, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        if isinstance(row, dict):
            writer.writerow(row)
    return parse_candidate_csv(csv_text.getvalue())


def validate_structure_text(text: str, fmt: str = "") -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not text or not text.strip():
        return [ValidationIssue("warning", "No structure supplied; structure-derived metrics will be unavailable.")]
    lines = [line for line in text.splitlines() if line.strip()]
    upper = text.upper()
    if fmt.lower() in {"pdb", ""} and not any(line.startswith(("ATOM", "HETATM", "MODEL")) for line in lines):
        if "data_" not in upper and "_atom_site." not in upper:
            issues.append(ValidationIssue("error", "No PDB ATOM/HETATM records or mmCIF atom_site table were found."))
    if fmt.lower() == "mmcif" and "_atom_site." not in upper and not any(line.startswith(("ATOM", "HETATM")) for line in lines):
        issues.append(ValidationIssue("error", "The mmCIF file does not contain an atom_site table."))
    return issues


def validation_summary(issues: Iterable[ValidationIssue]) -> Dict[str, int]:
    summary = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        summary[issue.level] = summary.get(issue.level, 0) + 1
    return summary
