import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

import pandas as pd


def project_json(project: Dict[str, Any], targets: List[Dict[str, Any]], candidates: List[Dict[str, Any]], analyses: List[Dict[str, Any]], feedback: List[Dict[str, Any]], audit: List[Dict[str, Any]]) -> bytes:
    payload = {"project": project, "targets": targets, "candidates": candidates, "analyses": analyses, "feedback": feedback, "audit": audit, "exported_at": datetime.now(timezone.utc).isoformat()}
    return json.dumps(payload, indent=2, default=str).encode()


def candidates_csv(candidates: Iterable[Dict[str, Any]]) -> bytes:
    rows = []
    for row in candidates:
        rows.append({k: row.get(k, "") for k in ["candidate_id", "sequence", "design_method", "generation_round", "structure_format"]})
    return pd.DataFrame(rows).to_csv(index=False).encode()


def feedback_template() -> bytes:
    columns = ["candidate_id", "binding_result", "kd_or_affinity", "expression", "solubility", "specificity", "functional_result", "assay_type", "replicates", "notes"]
    return (",".join(columns) + "\n").encode()


def project_zip(project: Dict[str, Any], targets: List[Dict[str, Any]], candidates: List[Dict[str, Any]], analyses: List[Dict[str, Any]], feedback: List[Dict[str, Any]], audit: List[Dict[str, Any]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", project_json(project, targets, candidates, analyses, feedback, audit))
        zf.writestr("candidates.csv", candidates_csv(candidates))
        zf.writestr("feedback_template.csv", feedback_template())
        for target in targets:
            if target.get("structure_text"):
                zf.writestr(f"structures/target_{target.get('name','target')}.{target.get('structure_format') or 'pdb'}", target["structure_text"])
        for candidate in candidates:
            if candidate.get("structure_text"):
                zf.writestr(f"structures/{candidate.get('candidate_id','candidate')}.{candidate.get('structure_format') or 'pdb'}", candidate["structure_text"])
    return buffer.getvalue()


def pdf_report(project: Dict[str, Any], targets: List[Dict[str, Any]], candidates: List[Dict[str, Any]], analyses: List[Dict[str, Any]], feedback: List[Dict[str, Any]], audit: List[Dict[str, Any]]) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.55 * inch, leftMargin=0.55 * inch, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = [Paragraph("ProteinDesign Insight report", styles["Title"]), Paragraph(f"Project: {project.get('name','')}", styles["Heading2"]), Paragraph("Computational triage report. Scores indicate priority for experimental testing and do not establish binding or biological activity.", styles["BodyText"]), Spacer(1, 10)]
    story.append(Paragraph("Scope and reproducibility", styles["Heading2"]))
    story.append(Paragraph(f"Target: {project.get('target','')} · Identifier: {project.get('identifier','')} · Candidates: {len(candidates)} · Analyses recorded: {len(analyses)} · Feedback records: {len(feedback)}", styles["BodyText"]))
    story.append(Paragraph("Inputs, parameters, pipeline version, model metadata, timestamps and audit events are preserved in the complete project ZIP and JSON export.", styles["BodyText"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Candidates and prioritization", styles["Heading2"]))
    rows = [["Candidate", "Length", "Structure", "Interface", "Priority", "Risks"]]
    for analysis in analyses:
        payload = analysis.get("payload", {})
        ranking = payload.get("ranking", {})
        rows.append([analysis.get("candidate_id"), payload.get("sequence", {}).get("length", "—"), "available" if payload.get("structure", {}).get("available") else "unavailable", "available" if payload.get("interface", {}).get("available") else "unavailable", ranking.get("score", "—"), "; ".join(ranking.get("risks", [])) or "—"])
    table = Table(rows, repeatRows=1, colWidths=[0.9*inch, 0.55*inch, 0.75*inch, 0.75*inch, 0.6*inch, 3.3*inch])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#149E9A")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), 0.25, colors.grey), ("VALIGN", (0,0), (-1,-1), "TOP"), ("FONTSIZE", (0,0), (-1,-1), 7)]))
    story.append(table)
    story.append(PageBreak())
    for title, body in [
        ("Target and structures", f"{len(targets)} target records supplied. Structure-derived values are only shown where parsable coordinates or supplied metadata exist."),
        ("Quality control and sequence", "Sequence length, composition, hydrophobic/charged fractions, unusual composition and clustering are calculated from supplied sequences."),
        ("Interface, specificity and conformation", "Contacts and interaction counts are geometric heuristics. Off-target and state comparisons require supplied structures and are not biological proof."),
        ("Diversity and uncertainty", "Sequence clustering and redundancy use pairwise identity. Uncertainty fields are only reported when supplied or calculated; unavailable values are not fabricated."),
        ("Experiments and failure analysis", "Experimental values are user-provided. Associations between observed outcomes and features are descriptive and not causal."),
        ("Limitations", "No docking, dynamics, wet-lab validation, or unsupported model inference is performed by this MVP. Review source inputs and rerun parameters before making an experimental decision."),
    ]:
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(body, styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()
