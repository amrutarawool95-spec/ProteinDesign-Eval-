import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


DB_PATH = os.environ.get("PDI_DB_PATH", "data/protein_design_insight.db")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Optional[str] = None) -> sqlite3.Connection:
    db_path = path or DB_PATH
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Optional[str] = None) -> None:
    with connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                target TEXT DEFAULT '',
                identifier TEXT DEFAULT '',
                design_method TEXT DEFAULT '',
                objective TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                is_demo INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                identifier TEXT DEFAULT '',
                sequence TEXT DEFAULT '',
                structure_text TEXT DEFAULT '',
                structure_format TEXT DEFAULT '',
                state TEXT DEFAULT 'primary',
                is_off_target INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}',
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                candidate_id TEXT NOT NULL,
                sequence TEXT NOT NULL,
                structure_text TEXT DEFAULT '',
                structure_format TEXT DEFAULT '',
                design_method TEXT DEFAULT '',
                generation_round TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                UNIQUE(project_id, candidate_id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                candidate_id TEXT NOT NULL,
                analysis_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                parameters_json TEXT DEFAULT '{}',
                pipeline_version TEXT DEFAULT '0.1.0',
                model_versions_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                candidate_id TEXT NOT NULL,
                binding_result TEXT DEFAULT '',
                kd_or_affinity TEXT DEFAULT '',
                expression TEXT DEFAULT '',
                solubility TEXT DEFAULT '',
                specificity TEXT DEFAULT '',
                functional_result TEXT DEFAULT '',
                assay_type TEXT DEFAULT '',
                replicates TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                source TEXT DEFAULT 'User provided',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                event_type TEXT NOT NULL,
                detail_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            """
        )


def one(query: str, params: Iterable[Any] = (), path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with connect(path) as conn:
        row = conn.execute(query, tuple(params)).fetchone()
        return dict(row) if row else None


def many(query: str, params: Iterable[Any] = (), path: Optional[str] = None) -> List[Dict[str, Any]]:
    with connect(path) as conn:
        return [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]


def execute(query: str, params: Iterable[Any] = (), path: Optional[str] = None) -> int:
    with connect(path) as conn:
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return int(cur.lastrowid or 0)


def create_project(data: Dict[str, Any], path: Optional[str] = None) -> int:
    now = utc_now()
    return execute(
        """INSERT INTO projects
        (name, description, target, identifier, design_method, objective, notes, is_demo, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("name", "Untitled project"),
            data.get("description", ""),
            data.get("target", ""),
            data.get("identifier", ""),
            data.get("design_method", ""),
            data.get("objective", ""),
            data.get("notes", ""),
            int(bool(data.get("is_demo", False))),
            now,
            now,
        ),
        path,
    )


def add_target(project_id: int, data: Dict[str, Any], path: Optional[str] = None) -> int:
    return execute(
        """INSERT INTO targets
        (project_id, name, identifier, sequence, structure_text, structure_format, state, is_off_target, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            project_id,
            data.get("name", "Target"),
            data.get("identifier", ""),
            data.get("sequence", ""),
            data.get("structure_text", ""),
            data.get("structure_format", ""),
            data.get("state", "primary"),
            int(bool(data.get("is_off_target", False))),
            json.dumps(data.get("metadata", {})),
        ),
        path,
    )


def add_candidate(project_id: int, data: Dict[str, Any], path: Optional[str] = None) -> int:
    return execute(
        """INSERT OR REPLACE INTO candidates
        (project_id, candidate_id, sequence, structure_text, structure_format, design_method, generation_round, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            project_id,
            data.get("candidate_id", ""),
            data.get("sequence", ""),
            data.get("structure_text", ""),
            data.get("structure_format", ""),
            data.get("design_method", ""),
            data.get("generation_round", ""),
            json.dumps(data.get("metadata", {})),
            utc_now(),
        ),
        path,
    )


def save_analysis(project_id: int, candidate_id: str, payload: Dict[str, Any], parameters: Dict[str, Any], path: Optional[str] = None) -> int:
    analysis_id = f"AN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    return execute(
        """INSERT INTO analyses
        (project_id, candidate_id, analysis_id, payload_json, parameters_json, model_versions_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (project_id, candidate_id, analysis_id, json.dumps(payload), json.dumps(parameters), json.dumps(payload.get("model_versions", {})), utc_now()),
        path,
    )


def save_feedback(project_id: int, rows: Iterable[Dict[str, Any]], path: Optional[str] = None) -> None:
    with connect(path) as conn:
        for row in rows:
            conn.execute(
                """INSERT INTO feedback
                (project_id, candidate_id, binding_result, kd_or_affinity, expression, solubility, specificity,
                 functional_result, assay_type, replicates, notes, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_id, row.get("candidate_id", ""), row.get("binding_result", ""),
                    row.get("kd_or_affinity", row.get("Kd or affinity", "")), row.get("expression", ""),
                    row.get("solubility", ""), row.get("specificity", ""), row.get("functional_result", ""),
                    row.get("assay_type", row.get("assay type", "")), row.get("replicates", ""),
                    row.get("notes", ""), row.get("source", "User provided"), utc_now(),
                ),
            )
        conn.commit()


def audit(project_id: Optional[int], event_type: str, detail: Dict[str, Any], path: Optional[str] = None) -> None:
    execute(
        "INSERT INTO audit_events (project_id, event_type, detail_json, created_at) VALUES (?, ?, ?, ?)",
        (project_id, event_type, json.dumps(detail), utc_now()),
        path,
    )


def get_project(project_id: int, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return one("SELECT * FROM projects WHERE id=?", (project_id,), path)


def list_projects(path: Optional[str] = None) -> List[Dict[str, Any]]:
    return many("SELECT * FROM projects ORDER BY updated_at DESC", path=path)


def get_targets(project_id: int, path: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = many("SELECT * FROM targets WHERE project_id=? ORDER BY is_off_target, id", (project_id,), path)
    for row in rows:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
    return rows


def get_candidates(project_id: int, path: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = many("SELECT * FROM candidates WHERE project_id=? ORDER BY candidate_id", (project_id,), path)
    for row in rows:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
    return rows


def get_analyses(project_id: int, path: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = many("SELECT * FROM analyses WHERE project_id=? ORDER BY created_at DESC", (project_id,), path)
    for row in rows:
        row["payload"] = json.loads(row.pop("payload_json"))
        row["parameters"] = json.loads(row.pop("parameters_json") or "{}")
    return rows


def get_feedback(project_id: int, path: Optional[str] = None) -> List[Dict[str, Any]]:
    return many("SELECT * FROM feedback WHERE project_id=? ORDER BY created_at DESC", (project_id,), path)


def get_audit(project_id: int, path: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = many("SELECT * FROM audit_events WHERE project_id=? ORDER BY created_at DESC", (project_id,), path)
    for row in rows:
        row["detail"] = json.loads(row.pop("detail_json") or "{}")
    return rows
