import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from .conformation import compare_conformations
from .demo import load_demo_project
from .diversity import diversity_analysis
from .feedback import normalize_feedback, summarize_feedback
from .interface import interface_metrics
from .ranking import DEFAULT_WEIGHTS, pareto_front, rank_bundles
from .report import candidates_csv, feedback_template, pdf_report, project_json, project_zip
from .sequence import sequence_metrics
from .specificity import compare_specificity
from .storage import (
    add_candidate, add_target, audit, get_analyses, get_audit, get_candidates, get_feedback,
    get_project, get_targets, init_db, list_projects, save_analysis, save_feedback,
)
from .structure import atom_table, structure_metrics
from .validation import (
    parse_candidate_csv, parse_candidate_json, parse_fasta, validate_structure_text, validation_summary,
)


APP_VERSION = "0.1.0"
PAGES = [
    "Dashboard", "Projects", "Targets", "Candidates", "Analysis", "Structures", "Interface",
    "Specificity", "Conformation", "Diversity", "Prioritization", "Experimental Feedback",
    "Failure Analysis", "Datasets", "Reports", "Documentation", "Settings",
]


def init_state() -> None:
    init_db()
    if "project_id" not in st.session_state:
        projects = list_projects()
        st.session_state.project_id = projects[0]["id"] if projects else None
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { max-width: 1440px; padding-top: 1.4rem; }
        [data-testid="stSidebar"] { border-right: 1px solid #0B1428; }
        [data-testid="stSidebar"] > div:first-child { background: #0D172C; }
        [data-testid="stSidebar"] * { color: #E6EEF7; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #B9C7D8; }
        [data-testid="stSidebar"] button { border-color: #263B5A; background: transparent; }
        [data-testid="stSidebar"] button:hover { border-color: #149E9A; color: #FFFFFF; }
        [data-testid="stSidebar"] [kind="header"] { color: #FFFFFF; }
        .pdi-brand { font-size: 1.45rem; font-weight: 800; letter-spacing: -0.03em; color: #F5FAFF; }
        .pdi-kicker { color: #149E9A; font-size: .75rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
        .pdi-note { border-left: 4px solid #149E9A; padding: .65rem .9rem; background: #EAF7F6; border-radius: .35rem; }
        .pdi-warning { border-left: 4px solid #D28B25; padding: .65rem .9rem; background: #FFF7E6; border-radius: .35rem; }
        .metric-card { background: white; border: 1px solid #DCE5EC; padding: .9rem; border-radius: .7rem; min-height: 95px; }
        div[data-testid="stMetric"] { background: white; border: 1px solid #DCE5EC; padding: .65rem; border-radius: .65rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_project() -> Optional[Dict[str, Any]]:
    project_id = st.session_state.get("project_id")
    return get_project(project_id) if project_id else None


def select_project_sidebar() -> None:
    projects = list_projects()
    with st.sidebar:
        st.markdown('<div class="pdi-brand">ProteinDesign Insight</div>', unsafe_allow_html=True)
        st.caption("Computational protein design triage")
        labels = ["No project"] + [f"{p['name']} · #{p['id']}" for p in projects]
        current = next((i for i, p in enumerate(projects, 1) if p["id"] == st.session_state.get("project_id")), 0)
        selected = st.selectbox("Active project", labels, index=current)
        if selected == "No project":
            st.session_state.project_id = None
        else:
            st.session_state.project_id = projects[labels.index(selected) - 1]["id"]
        active = safe_project()
        if active:
            st.markdown(
                f"<div style='background:#162642;border:1px solid #263B5A;border-radius:8px;padding:10px 12px;margin:8px 0 14px;'>"
                f"<div style='font-size:10px;color:#91A5BE;text-transform:uppercase;letter-spacing:.08em;'>Active project</div>"
                f"<div style='font-weight:700;color:#FFFFFF;margin-top:3px;'>{active['name']}</div>"
                f"<div style='font-size:11px;color:#AFC0D3;margin-top:4px;'>{active['identifier'] or 'Identifier not set'}</div></div>",
                unsafe_allow_html=True,
            )
        st.divider()
        st.markdown("**Workflow**")
        for page in PAGES:
            if st.button(page, key=f"nav_{page}", use_container_width=True, type="secondary" if st.session_state.page != page else "primary"):
                st.session_state.page = page
                st.rerun()
        st.divider()
        demo_mode = st.toggle("Demo Mode", value=True, help="Marks synthetic fixtures and keeps their illustrative status visible.")
        st.session_state.demo_mode = demo_mode
        if st.button("Load Demo Project", use_container_width=True):
            st.session_state.project_id = load_demo_project()
            st.session_state.page = "Dashboard"
            st.success("Illustrative demo project loaded.")
            st.rerun()
        if st.button("System Health", use_container_width=True):
            st.session_state.page = "Settings"
            st.rerun()


def header(title: str, subtitle: str = "") -> None:
    st.markdown('<div class="pdi-kicker">ProteinDesign Insight · research triage</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    project = safe_project()
    if project and project.get("is_demo"):
        st.markdown('<div class="pdi-warning"><b>Illustrative demo project.</b> Synthetic fixtures are for workflow testing and are not real structures, predictions, or experiments.</div>', unsafe_allow_html=True)


def download_test_data() -> None:
    demo_dir = Path(__file__).resolve().parent.parent / "data" / "demo"
    st.download_button("Download Demo Dataset", (demo_dir / "candidates.csv").read_bytes(), "protein_design_insight_demo_candidates.csv", "text/csv", use_container_width=True)
    st.download_button("Download Test Template", b"candidate_id,sequence,design_method,generation_round,structure_format,structure\n", "candidate_upload_template.csv", "text/csv", use_container_width=True)
    st.download_button("Download Feedback Template", feedback_template(), "experimental_feedback_template.csv", "text/csv", use_container_width=True)


def make_analysis(candidate: Dict[str, Any], project_id: int, targets: List[Dict[str, Any]], all_candidates: List[Dict[str, Any]], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    primary = next((target for target in targets if not target["is_off_target"]), targets[0] if targets else {})
    states = [target for target in targets if not target["is_off_target"]]
    off_targets = [target for target in targets if target["is_off_target"]]
    structure = structure_metrics(candidate.get("structure_text", ""), candidate.get("structure_format", ""), candidate.get("sequence", ""))
    interface = interface_metrics(primary.get("structure_text", ""), candidate.get("structure_text", ""), primary.get("structure_format", ""), candidate.get("structure_format", ""))
    specificity = compare_specificity(candidate, primary, off_targets)
    conformation = compare_conformations(candidate, states)
    diversity = diversity_analysis(all_candidates)
    sequence = sequence_metrics(candidate.get("sequence", ""))
    uncertainty = {
        "plddt": structure.get("plddt"),
        "pae": structure.get("pae"),
        "bfactor_mean": structure.get("bfactor_mean"),
        "available_fields": [key for key in ("plddt", "pae", "bfactor_mean") if structure.get(key) is not None],
        "note": "Only supplied or calculated fields are shown. Missing model uncertainty is not imputed.",
    }
    bundle = {"candidate_id": candidate["candidate_id"], "sequence": sequence, "structure": structure, "interface": interface, "specificity": specificity, "conformation": conformation, "diversity": diversity, "uncertainty": uncertainty}
    ranking = rank_bundles([bundle], weights)[0]
    bundle["ranking"] = ranking
    bundle["model_versions"] = {"pipeline": APP_VERSION, "structure_predictor": "not run", "interface_method": "coordinate heuristic"}
    return bundle


def run_all_analyses(project_id: int, weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    candidates = get_candidates(project_id)
    targets = get_targets(project_id)
    saved = []
    for candidate in candidates:
        payload = make_analysis(candidate, project_id, targets, candidates, weights)
        save_analysis(project_id, candidate["candidate_id"], payload, {"weights": weights or DEFAULT_WEIGHTS, "inputs": {"target_ids": [t["id"] for t in targets], "candidate_id": candidate["candidate_id"]}})
        saved.append(payload)
    audit(project_id, "analysis_run", {"candidate_count": len(candidates), "pipeline_version": APP_VERSION})
    return saved


def analysis_payloads(project_id: int) -> List[Dict[str, Any]]:
    return [row["payload"] for row in get_analyses(project_id)]


def render_dashboard() -> None:
    project = safe_project()
    header("Dashboard", "A transparent triage workspace for deciding what to test next.")
    if not project:
        st.info("Create a project or load the illustrative demo to begin.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start with Demo Project", type="primary", use_container_width=True):
                st.session_state.project_id = load_demo_project()
                st.rerun()
        with col2:
            download_test_data()
        return
    candidates = get_candidates(project["id"])
    targets = get_targets(project["id"])
    analyses = get_analyses(project["id"])
    feedback = get_feedback(project["id"])
    scores = [{"candidate_id": row["candidate_id"], "score": row["payload"].get("ranking", {}).get("score")} for row in analyses]
    top = sorted([r for r in scores if r["score"] is not None], key=lambda r: r["score"], reverse=True)[:5]
    cols = st.columns(5)
    for col, label, value in zip(cols, ["Candidates", "Targets", "Analyses", "Feedback", "Warnings"], [len(candidates), len(targets), len(analyses), len(feedback), sum(len(a["payload"].get("ranking", {}).get("risks", [])) for a in analyses)]):
        col.metric(label, value)
    st.subheader("Project status")
    st.write(project["description"] or "No description provided.")
    st.caption(f"Objective: {project['objective'] or 'Not specified'} · Target: {project['target'] or 'Not specified'} · Identifier: {project['identifier'] or 'Not specified'}")
    if not analyses:
        st.markdown('<div class="pdi-note">Upload candidates, validate them, then run the analysis pipeline. Unavailable metrics will stay unavailable instead of being filled with guesses.</div>', unsafe_allow_html=True)
        if st.button("Run analysis for current candidates", type="primary", disabled=not candidates):
            run_all_analyses(project["id"])
            st.rerun()
    else:
        st.subheader("Top computational priorities")
        st.dataframe(pd.DataFrame(top), use_container_width=True, hide_index=True)
        if top:
            st.bar_chart(pd.DataFrame(top).set_index("candidate_id"))
    st.subheader("Workflow")
    st.progress(min(1.0, len(analyses) / max(len(candidates), 1)), text=f"{len(analyses)}/{len(candidates)} candidates analyzed")
    st.caption("Priority scores are for experimental testing triage, not guaranteed binding or biological activity.")


def render_projects() -> None:
    header("Projects", "Create projects that preserve inputs, parameters, analyses, feedback, and audit history.")
    projects = list_projects()
    if projects:
        st.dataframe(pd.DataFrame(projects)[["id", "name", "target", "identifier", "is_demo", "updated_at"]], use_container_width=True, hide_index=True)
    with st.form("new_project"):
        name = st.text_input("Project name", "New protein design project")
        description = st.text_area("Description")
        c1, c2 = st.columns(2)
        target = c1.text_input("Target")
        identifier = c2.text_input("Target identifier")
        design_method = st.text_input("Design method")
        objective = st.text_input("Objective", "Prioritize candidates for experimental testing")
        notes = st.text_area("Notes")
        if st.form_submit_button("Create project", type="primary"):
            if not name.strip():
                st.error("Project name is required.")
            else:
                st.session_state.project_id = __import__("core.storage", fromlist=["create_project"]).create_project({"name": name, "description": description, "target": target, "identifier": identifier, "design_method": design_method, "objective": objective, "notes": notes})
                audit(st.session_state.project_id, "project_created", {"name": name})
                st.success("Project created.")
                st.rerun()


def render_targets() -> None:
    project = safe_project()
    header("Targets", "Primary target states and optional off-targets; structures and identifiers are kept separate from claims.")
    if not project:
        st.info("Select or create a project first.")
        return
    targets = get_targets(project["id"])
    if targets:
        st.dataframe(pd.DataFrame([{**t, "structure_text": "supplied" if t["structure_text"] else "unavailable"} for t in targets])[["name", "identifier", "state", "is_off_target", "structure_text"]], use_container_width=True, hide_index=True)
    with st.expander("Add target or state"):
        with st.form("add_target"):
            name = st.text_input("Name")
            identifier = st.text_input("PDB, mmCIF, FASTA, or UniProt identifier")
            state = st.text_input("State", "primary")
            off_target = st.checkbox("Off-target")
            structure_file = st.file_uploader("Structure (PDB/mmCIF)", type=["pdb", "ent", "cif", "mmcif"], key="target_structure")
            sequence_file = st.file_uploader("Sequence (FASTA)", type=["fasta", "fa"], key="target_sequence")
            if st.form_submit_button("Save target"):
                structure_text = structure_file.getvalue().decode(errors="replace") if structure_file else ""
                sequence = sequence_file.getvalue().decode(errors="replace") if sequence_file else ""
                issues = validate_structure_text(structure_text, structure_file.name.split(".")[-1] if structure_file else "")
                for issue in issues:
                    (st.error if issue.level == "error" else st.warning)(issue.message)
                if not any(issue.level == "error" for issue in issues):
                    add_target(project["id"], {"name": name or "Target", "identifier": identifier, "state": state, "is_off_target": off_target, "structure_text": structure_text, "structure_format": structure_file.name.split(".")[-1] if structure_file else "", "sequence": sequence})
                    audit(project["id"], "target_added", {"name": name, "identifier": identifier})
                    st.success("Target saved.")
                    st.rerun()


def render_candidates() -> None:
    project = safe_project()
    header("Candidates", "Upload FASTA, CSV, or JSON candidate records and validate before they enter the analysis set.")
    if not project:
        st.info("Select or create a project first.")
        return
    candidates = get_candidates(project["id"])
    if candidates:
        st.dataframe(pd.DataFrame([{**c, "sequence": c["sequence"][:18] + ("…" if len(c["sequence"]) > 18 else ""), "structure_text": "supplied" if c["structure_text"] else "unavailable"} for c in candidates])[["candidate_id", "sequence", "design_method", "generation_round", "structure_text"]], use_container_width=True, hide_index=True)
    uploaded = st.file_uploader("Upload My Dataset", type=["csv", "json", "fasta", "fa"], key="candidate_upload")
    structure_files = st.file_uploader("Optional structure files", type=["pdb", "ent", "cif", "mmcif"], accept_multiple_files=True, key="candidate_structures")
    if uploaded:
        raw = uploaded.getvalue().decode(errors="replace")
        if uploaded.name.lower().endswith(".csv"):
            rows, issues = parse_candidate_csv(raw)
        elif uploaded.name.lower().endswith(".json"):
            rows, issues = parse_candidate_json(raw)
        else:
            fasta, issues = parse_fasta(raw)
            rows = [__import__("core.models", fromlist=["CandidateRecord"]).CandidateRecord(candidate_id=cid, sequence=seq) for cid, seq in fasta]
        summary = validation_summary(issues)
        st.write(f"Validation: {summary['error']} errors · {summary['warning']} warnings")
        for issue in issues:
            (st.error if issue.level == "error" else st.warning)(issue.message)
        preview = pd.DataFrame([{"candidate_id": row.candidate_id, "length": len(row.sequence), "design_method": row.design_method, "structure": "supplied" if row.structure_text else "unavailable"} for row in rows])
        st.dataframe(preview, use_container_width=True, hide_index=True)
        if st.button("Import validated candidates", type="primary", disabled=not rows or summary["error"] > 0):
            structure_map = {Path(f.name).stem: f.getvalue().decode(errors="replace") for f in structure_files}
            for row in rows:
                add_candidate(project["id"], {"candidate_id": row.candidate_id, "sequence": row.sequence, "design_method": row.design_method, "generation_round": row.generation_round, "structure_text": row.structure_text or structure_map.get(row.candidate_id, ""), "structure_format": row.structure_format or ("pdb" if row.candidate_id in structure_map else ""), "metadata": row.metadata})
            audit(project["id"], "candidate_import", {"filename": uploaded.name, "count": len(rows), "validation": summary})
            st.success(f"Imported {len(rows)} candidates.")
            st.rerun()


def render_analysis() -> None:
    project = safe_project()
    header("Analysis", "Run the independent analysis pipeline and inspect source-level availability for every metric.")
    if not project:
        st.info("Select a project first.")
        return
    candidates, targets = get_candidates(project["id"]), get_targets(project["id"])
    if st.button("Analyze all candidates", type="primary", disabled=not candidates or not targets):
        run_all_analyses(project["id"])
        st.success("Analysis completed and recorded with an analysis ID.")
        st.rerun()
    analyses = get_analyses(project["id"])
    if not analyses:
        st.info("No analysis runs recorded yet.")
        return
    rows = []
    for row in analyses:
        p = row["payload"]
        rows.append({"candidate_id": row["candidate_id"], "analysis_id": row["analysis_id"], "length": p.get("sequence", {}).get("length"), "structure": "Available" if p.get("structure", {}).get("available") else "Unavailable", "interface": "Available" if p.get("interface", {}).get("available") else "Unavailable", "score": p.get("ranking", {}).get("score"), "created_at": row["created_at"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    candidate = st.selectbox("Candidate detail", [row["candidate_id"] for row in analyses])
    chosen = next(row for row in analyses if row["candidate_id"] == candidate)
    show_analysis_detail(chosen["payload"])


def show_analysis_detail(payload: Dict[str, Any]) -> None:
    st.subheader(f"Candidate {payload.get('candidate_id')}")
    p = payload
    tabs = st.tabs(["Sequence", "Structure", "Interface", "Specificity", "Conformation", "Diversity", "Uncertainty", "Priority"])
    with tabs[0]:
        st.json(p.get("sequence", {}))
    with tabs[1]:
        st.json(p.get("structure", {}))
    with tabs[2]:
        st.json(p.get("interface", {}))
    with tabs[3]:
        st.json(p.get("specificity", {}))
    with tabs[4]:
        st.json(p.get("conformation", {}))
    with tabs[5]:
        st.json(p.get("diversity", {}))
    with tabs[6]:
        st.json(p.get("uncertainty", {}))
    with tabs[7]:
        ranking = p.get("ranking", {})
        st.metric("Experimental Priority Score", ranking.get("score", "Unavailable"))
        st.caption(ranking.get("meaning"))
        st.dataframe(pd.DataFrame([{"metric": k, "normalized_value": v, "weighted_contribution": ranking.get("contributions", {}).get(k)} for k, v in ranking.get("components", {}).items()]), use_container_width=True, hide_index=True)
        if ranking.get("risks"):
            st.warning(" · ".join(ranking["risks"]))


def render_structures() -> None:
    project = safe_project()
    header("Structures", "Inspect supplied coordinates with a guarded 3D viewer; invalid or missing structures remain explicit.")
    if not project:
        return
    candidates, targets = get_candidates(project["id"]), get_targets(project["id"])
    options = [f"Target · {t['name']}" for t in targets if t["structure_text"]] + [f"Candidate · {c['candidate_id']}" for c in candidates if c["structure_text"]]
    if not options:
        st.info("No structures are available.")
        return
    selected = st.selectbox("Structure", options)
    if selected.startswith("Target"):
        item = next(t for t in targets if f"Target · {t['name']}" == selected)
    else:
        item = next(c for c in candidates if f"Candidate · {c['candidate_id']}" == selected)
    atoms = atom_table(item["structure_text"], item.get("structure_format", ""))
    st.caption(f"{len(atoms)} parsed atoms · {len({(a['chain'], a['residue_number']) for a in atoms})} residues")
    pdb = item["structure_text"]
    viewer_html = f"""<div id='viewer' style='height:460px;width:100%;position:relative;'></div>
    <script src='https://3dmol.csb.pitt.edu/build/3Dmol-min.js'></script>
    <script>
    const el = document.getElementById('viewer');
    const viewer = $3Dmol.createViewer(el, {{backgroundColor:'#f7fafc'}});
    viewer.addModel({json.dumps(pdb)}, 'pdb');
    viewer.setStyle({{}}, {{cartoon: {{color:'spectrum'}}, stick: {{radius:0.12}}}});
    viewer.zoomTo(); viewer.render();
    </script>"""
    try:
        components.html(viewer_html, height=480, scrolling=False)
    except Exception:
        st.warning("The 3D viewer could not render this structure in the current browser.")
    st.download_button("Download structure", pdb, f"{selected.replace(' ', '_')}.pdb", "chemical/x-pdb")


def render_interface_like(page: str) -> None:
    project = safe_project()
    header(page, "Computed summaries are shown only when the required input structures and metadata are available.")
    if not project:
        return
    analyses = get_analyses(project["id"])
    if not analyses:
        st.info("Run Analysis first.")
        return
    rows = []
    for a in analyses:
        p = a["payload"]
        section = {"Interface": "interface", "Specificity": "specificity", "Conformation": "conformation"}.get(page, "diversity")
        data = p.get(section, {})
        rows.append({"candidate_id": a["candidate_id"], "available": data.get("available"), "classification": data.get("classification", data.get("risk", "")), "contacts": data.get("contacts", data.get("primary_contacts", ""))})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    selected = st.selectbox("Inspect candidate", [a["candidate_id"] for a in analyses], key=f"{page}_candidate")
    payload = next(a["payload"] for a in analyses if a["candidate_id"] == selected)
    st.json(payload.get({"Interface": "interface", "Specificity": "specificity", "Conformation": "conformation", "Diversity": "diversity"}[page], {}))


def render_prioritization() -> None:
    project = safe_project()
    header("Prioritization", "Adjust transparent weights, apply constraints, inspect Pareto candidates, and choose a diverse experimental batch.")
    if not project:
        return
    analyses = get_analyses(project["id"])
    if not analyses:
        st.info("Run Analysis first.")
        return
    with st.expander("Scoring weights", expanded=True):
        cols = st.columns(4)
        weights = {}
        for i, key in enumerate(DEFAULT_WEIGHTS):
            weights[key] = cols[i % 4].slider(key.replace("_", " ").title(), 0.0, 1.0, float(DEFAULT_WEIGHTS[key]), 0.05, key=f"weight_{key}")
        total = sum(weights.values())
        st.caption(f"Raw weight total: {total:.2f}. Scores normalize over available metrics; unavailable inputs are not imputed.")
    c1, c2 = st.columns(2)
    max_length = c1.number_input("Maximum sequence length constraint", min_value=0, value=0)
    exclude_clashes = c2.checkbox("Exclude candidates with coordinate clashes")
    bundles = [a["payload"] for a in analyses]
    ranked = rank_bundles(bundles, weights, {"max_length": max_length or None, "exclude_clashes": exclude_clashes})
    table = []
    for row in ranked:
        table.append({"candidate_id": row["candidate_id"], "score": row["score"], "eligible": row["eligible"], "risks": "; ".join(row["risks"])})
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    pareto = pareto_front(ranked)
    st.info(f"Pareto candidates across available interface and structure dimensions: {', '.join(pareto) or 'none'}")
    st.caption("Scores rank testing priority only. They do not predict binding, specificity, expression, or therapeutic performance.")


def render_feedback() -> None:
    project = safe_project()
    header("Experimental Feedback", "Record observed assay outcomes separately from calculated predictions.")
    if not project:
        return
    candidates = get_candidates(project["id"])
    with st.form("manual_feedback"):
        cid = st.selectbox("Candidate ID", [c["candidate_id"] for c in candidates] or [""])
        c1, c2, c3 = st.columns(3)
        binding = c1.selectbox("Binding result", ["unknown", "positive", "negative"])
        kd = c2.text_input("Kd or affinity")
        assay = c3.text_input("Assay type")
        expression = st.text_input("Expression")
        solubility = st.text_input("Solubility")
        specificity = st.text_input("Specificity observation")
        functional = st.text_input("Functional result")
        replicates = st.text_input("Replicates")
        notes = st.text_area("Notes")
        if st.form_submit_button("Add experimental record", type="primary"):
            save_feedback(project["id"], [{"candidate_id": cid, "binding_result": binding, "kd_or_affinity": kd, "assay_type": assay, "expression": expression, "solubility": solubility, "specificity": specificity, "functional_result": functional, "replicates": replicates, "notes": notes}])
            audit(project["id"], "feedback_added", {"candidate_id": cid})
            st.success("Experimental record saved as User provided.")
            st.rerun()
    uploaded = st.file_uploader("Import feedback CSV", type=["csv"], key="feedback_upload")
    if uploaded:
        try:
            rows = pd.read_csv(uploaded).fillna("").to_dict("records")
            normalized = normalize_feedback(rows)
            invalid = [row for row in normalized if row.get("candidate_id") not in {c["candidate_id"] for c in candidates}]
            if invalid:
                st.error(f"{len(invalid)} rows refer to candidate IDs not in this project.")
            if st.button("Import feedback rows", disabled=bool(invalid)):
                save_feedback(project["id"], normalized)
                audit(project["id"], "feedback_import", {"filename": uploaded.name, "count": len(normalized)})
                st.success(f"Imported {len(normalized)} feedback rows.")
                st.rerun()
        except Exception as exc:
            st.error(f"Could not read feedback CSV: {exc}")
    feedback = get_feedback(project["id"])
    if feedback:
        st.dataframe(pd.DataFrame(feedback), use_container_width=True, hide_index=True)
        st.caption("Experimental is user-provided here; values are never used to rewrite calculated metrics.")


def render_failure_analysis() -> None:
    project = safe_project()
    header("Failure Analysis", "Compare observed outcomes and retain failure memory without making unsupported causal claims.")
    if not project:
        return
    summary = summarize_feedback(get_feedback(project["id"]), get_analyses(project["id"]))
    cols = st.columns(4)
    for col, label in zip(cols, ["Total labeled", "Observed success", "Observed failure", "Unlabeled"]):
        col.metric(label, summary[{"Total labeled": "n_total", "Observed success": "n_success", "Observed failure": "n_failure", "Unlabeled": "unlabeled"}[label]])
    st.info(summary["model_note"])
    if summary["failure_features"]:
        st.dataframe(pd.DataFrame(summary["failure_features"]), use_container_width=True, hide_index=True)
    else:
        st.caption("No negative experimental records yet. Failure Memory will appear after observed feedback is added.")


def render_datasets() -> None:
    project = safe_project()
    header("Datasets", "Search, filter, batch export, and preserve the combined candidate/analysis/feedback dataset.")
    if not project:
        return
    candidates, analyses, feedback = get_candidates(project["id"]), get_analyses(project["id"]), get_feedback(project["id"])
    analysis_map = {a["candidate_id"]: a["payload"] for a in analyses}
    feedback_map = {f["candidate_id"]: f for f in feedback}
    rows = []
    for c in candidates:
        p = analysis_map.get(c["candidate_id"], {})
        rows.append({"candidate_id": c["candidate_id"], "length": len(c["sequence"]), "priority_score": p.get("ranking", {}).get("score"), "binding_result": feedback_map.get(c["candidate_id"], {}).get("binding_result", "unavailable"), "structure_available": p.get("structure", {}).get("available", False)})
    query = st.text_input("Search candidate ID")
    df = pd.DataFrame(rows)
    if query:
        df = df[df["candidate_id"].str.contains(query, case=False, na=False)]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Export dataset CSV", df.to_csv(index=False).encode(), "protein_design_insight_dataset.csv", "text/csv")


def render_reports() -> None:
    project = safe_project()
    header("Reports", "Export reproducible project artifacts, JSON audit trails, FASTA/CSV datasets, PDF reports, or a complete ZIP.")
    if not project:
        return
    targets, candidates, analyses, feedback, audit_rows = get_targets(project["id"]), get_candidates(project["id"]), get_analyses(project["id"]), get_feedback(project["id"]), get_audit(project["id"])
    st.download_button("Export project JSON", project_json(project, targets, candidates, analyses, feedback, audit_rows), "protein_design_insight_project.json", "application/json", use_container_width=True)
    st.download_button("Export candidates CSV", candidates_csv(candidates), "protein_design_insight_candidates.csv", "text/csv", use_container_width=True)
    st.download_button("Export PDF report", pdf_report(project, targets, candidates, analyses, feedback, audit_rows), "protein_design_insight_report.pdf", "application/pdf", use_container_width=True)
    st.download_button("Export complete project ZIP", project_zip(project, targets, candidates, analyses, feedback, audit_rows), "protein_design_insight_project.zip", "application/zip", use_container_width=True)
    st.subheader("Audit history")
    if audit_rows:
        st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)


def render_documentation() -> None:
    header("Documentation", "Operating notes for researchers and future pipeline extensions.")
    st.markdown(
        """
        **Interpretation guardrails**

        - **Calculated** values come from supplied sequences or coordinates.
        - **Model derived** values are shown only when supplied as metadata; pLDDT and PAE are never inferred.
        - **Experimental** values are user-provided assay observations.
        - **Unavailable** means the required input was not supplied or a calculation could not be completed.
        - Priority is a transparent decision aid for selecting experiments, not a guarantee of binding.

        **Supported MVP inputs**

        FASTA, candidate CSV/JSON, PDB and common mmCIF atom-site loops. The parser fails locally with a readable validation message and never exposes a traceback in normal use.

        **Extending the system**

        Add model runners behind `core/structure.py` or separate adapters, persist their version and parameters in `analyses`, and preserve the distinction between predictions and observations. The SQLite schema is intentionally portable to PostgreSQL.
        """
    )


def render_settings() -> None:
    header("Settings & System Health", "Check the local runtime, dependencies, database, storage, analysis engine, and viewer readiness.")
    import sys
    checks = []
    for name, status, detail in [
        ("Python", True, sys.version.split()[0]),
        ("Streamlit", True, getattr(st, "__version__", "loaded")),
        ("Database", bool(os.path.exists(os.environ.get("PDI_DB_PATH", "data/protein_design_insight.db"))), os.environ.get("PDI_DB_PATH", "data/protein_design_insight.db")),
        ("Storage", os.access("data", os.W_OK), "data/ writable"),
        ("Analysis engine", True, f"pipeline {APP_VERSION}"),
        ("3D viewer", True, "3Dmol.js browser component with graceful fallback"),
    ]:
        checks.append({"component": name, "status": "Ready" if status else "Needs attention", "detail": detail})
    st.dataframe(pd.DataFrame(checks), use_container_width=True, hide_index=True)
    st.caption("No secrets or external APIs are required. Dependency health is determined by successful imports in this process.")


def render_page(page: str) -> None:
    functions = {
        "Dashboard": render_dashboard, "Projects": render_projects, "Targets": render_targets, "Candidates": render_candidates,
        "Analysis": render_analysis, "Structures": render_structures, "Interface": lambda: render_interface_like("Interface"),
        "Specificity": lambda: render_interface_like("Specificity"), "Conformation": lambda: render_interface_like("Conformation"),
        "Diversity": lambda: render_interface_like("Diversity"), "Prioritization": render_prioritization,
        "Experimental Feedback": render_feedback, "Failure Analysis": render_failure_analysis, "Datasets": render_datasets,
        "Reports": render_reports, "Documentation": render_documentation, "Settings": render_settings,
    }
    functions.get(page, render_dashboard)()


def run_app() -> None:
    init_state()
    inject_css()
    select_project_sidebar()
    render_page(st.session_state.page)
