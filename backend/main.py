"""ProteinDesign-Eval API entry point.

The demo frontend is intentionally usable without the API. This service is the
extensible boundary for real project persistence, background analysis jobs, and
reproducible exports.
"""
from datetime import datetime, timezone
from typing import Any
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="ProteinDesign-Eval API", version="0.4.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PROJECT = {
    "id": "PDE-2026-00017",
    "name": "Human D2R de novo Miniprotein",
    "target": "DRD2",
    "candidate_count": 120,
    "status": "completed",
}
ANALYSIS = {
    "id": "PDE-A-0042",
    "pipeline_version": "0.4.1",
    "status": "completed",
    "created_at": "2026-09-26T16:38:00Z",
    "modules": ["sequence", "structure", "interface", "specificity", "conformation", "diversity", "ranking"],
}

class ExperimentalResult(BaseModel):
    candidate_id: str
    binding_result: str
    kd: float | None = None
    expression: str | None = None
    solubility: str | None = None
    specificity: str | None = None
    function: str | None = None
    conditions: str | None = None
    notes: str | None = None

class AnalysisRequest(BaseModel):
    candidate_ids: list[str] = Field(default_factory=list)
    target_ids: list[str] = Field(default_factory=list)
    weights: dict[str, float] = Field(default_factory=dict)
    pipeline_version: str = "0.4.1"

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "protein-design-eval"}

@app.get("/projects")
def projects() -> list[dict[str, Any]]:
    return [PROJECT]

@app.get("/projects/{project_id}")
def project(project_id: str) -> dict[str, Any]:
    return {**PROJECT, "id": project_id}

@app.get("/targets")
def targets() -> list[dict[str, Any]]:
    return [
        {"id": "DRD2", "label": "Primary target", "states": ["active", "inactive", "intermediate"], "source": "PDB"},
        {"id": "ADRB2", "label": "Related receptor", "states": ["active"], "source": "PDB"},
        {"id": "5HT2A", "label": "Off-target", "states": ["active"], "source": "UniProt"},
    ]

@app.get("/candidates")
def candidates(project_id: str | None = None) -> dict[str, Any]:
    return {"project_id": project_id or PROJECT["id"], "count": PROJECT["candidate_count"], "items": []}

@app.get("/analyses")
def analyses(project_id: str | None = None) -> list[dict[str, Any]]:
    return [{**ANALYSIS, "project_id": project_id or PROJECT["id"]}]

@app.post("/analyses", status_code=202)
def create_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    analysis_id = f"PDE-A-{datetime.now(timezone.utc).strftime('%H%M%S')}"
    background_tasks.add_task(_queue_analysis, analysis_id)
    return {"id": analysis_id, "status": "queued", "request": request.model_dump()}

@app.get("/experimental-results")
def experimental_results(project_id: str | None = None) -> dict[str, Any]:
    return {"project_id": project_id or PROJECT["id"], "count": 20, "items": []}

@app.post("/experimental-results", status_code=201)
def add_experimental_result(result: ExperimentalResult) -> dict[str, Any]:
    return {"id": f"EXP-{result.candidate_id}", "record": result.model_dump(), "label": "Experimental"}

@app.get("/failure-analysis")
def failure_analysis(project_id: str | None = None) -> dict[str, Any]:
    return {"project_id": project_id or PROJECT["id"], "interpretation": "association_only", "patterns": []}

@app.get("/datasets")
def datasets() -> list[dict[str, Any]]:
    return [
        {"id": "demo-gpcr-v4", "type": "candidate_library", "version": "4", "count": 120},
        {"id": "drd2-states", "type": "target_structures", "version": "1", "count": 3},
    ]

@app.get("/reports")
def reports(project_id: str | None = None) -> list[dict[str, Any]]:
    return [{"id": "PDE-R-0042", "analysis_id": ANALYSIS["id"], "formats": ["pdf", "json", "csv", "fasta"]}]

@app.get("/exports/{export_type}")
def export(export_type: str) -> dict[str, Any]:
    return {"export_type": export_type, "status": "ready", "analysis_id": ANALYSIS["id"]}

def _queue_analysis(analysis_id: str) -> None:
    # Replace with Celery/RQ/Arq worker integration in production.
    return None