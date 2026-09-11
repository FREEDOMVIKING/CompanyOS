from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"

TRACE_REPORT = RUNTIME / "profit_first_orchestration_trace_report.json"
EXPANSION_STATE = RUNTIME / "profit_first_enrichment_expansion_state.json"
MATERIALIZATION_REPORT = RUNTIME / "candidate_materialization_report.json"
EVIDENCE_REPORT = RUNTIME / "profit_first_evidence_report.json"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"

SEARCH_ROOTS = [
    ROOT / "workspace",
    ROOT / "artifacts",
    ROOT / "exports",
    ROOT / "companyos_runtime",
    ROOT / ".companyos_runtime",
]

JOURNALS = [
    ROOT / "companyos_runtime" / "full_autonomy_journal.jsonl",
    ROOT / ".companyos_runtime" / "full_autonomy_journal.jsonl",
    ROOT / "companyos_runtime" / "ceo_orchestration_journal.jsonl",
    ROOT / ".companyos_runtime" / "ceo_orchestration_journal.jsonl",
    ROOT / "companyos_runtime" / "canonical_production" / "journal.jsonl",
    ROOT / ".companyos_runtime" / "canonical_production" / "journal.jsonl",
]

def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def latest_expansion_orchestration_id() -> str | None:
    st = load(EXPANSION_STATE, {})
    runs = st.get("runs") or []
    for r in reversed(runs):
        if r.get("stage") == "opportunity_expansion" and r.get("orchestration_id"):
            return str(r["orchestration_id"])
    return None

def _scan_obj(obj: Any, oid: str, source: str, hits: list[dict], path="$"):
    if isinstance(obj, dict):
        text = json.dumps(obj, default=str)
        if oid in text:
            hits.append({
                "source": source,
                "path": path,
                "object": obj,
            })
        for k, v in obj.items():
            _scan_obj(v, oid, source, hits, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan_obj(v, oid, source, hits, f"{path}[{i}]")

def _jsonl_hits(path: Path, oid: str, max_lines=5000) -> list[dict]:
    hits = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-max_lines:]
    except Exception:
        return hits
    for idx, line in enumerate(lines, 1):
        if oid not in line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            obj = {"raw": line[:12000]}
        hits.append({
            "source": str(path.relative_to(ROOT)),
            "line_from_tail_window": idx,
            "object": obj,
        })
    return hits

def trace(oid: str | None = None) -> dict:
    oid = oid or latest_expansion_orchestration_id()
    if not oid:
        report = {"ok": False, "reason": "no_opportunity_expansion_orchestration_id_found"}
        save(TRACE_REPORT, report)
        return report

    journal_hits = []
    for p in JOURNALS:
        if p.exists():
            journal_hits.extend(_jsonl_hits(p, oid))

    artifact_hits = []
    scanned = 0
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.json"):
            if scanned >= 3000:
                break
            scanned += 1
            try:
                rel = str(p.relative_to(ROOT))
            except Exception:
                rel = str(p)
            if rel.endswith("profit_first_orchestration_trace_report.json"):
                continue
            obj = load(p, None)
            if obj is None:
                continue
            _scan_obj(obj, oid, rel, artifact_hits)

    candidate_files = sorted(CANDIDATE_DIR.glob("*.json")) if CANDIDATE_DIR.exists() else []
    candidates = []
    for p in candidate_files:
        obj = load(p, {})
        candidates.append({
            "file": str(p.relative_to(ROOT)),
            "name": obj.get("name"),
            "sector": obj.get("sector"),
            "business_model": obj.get("business_model"),
            "orchestration_id": obj.get("orchestration_id"),
            "evidence_confidence": obj.get("evidence_confidence"),
            "materialized_from": obj.get("materialized_from"),
        })

    tied_candidates = [
        c for c in candidates
        if c.get("orchestration_id") and str(c["orchestration_id"]) == oid
    ]

    evidence = load(EVIDENCE_REPORT, {})
    materialization = load(MATERIALIZATION_REPORT, {})

    report = {
        "generated_at_unix": time.time(),
        "orchestration_id": oid,
        "journal_hit_count": len(journal_hits),
        "artifact_hit_count": len(artifact_hits),
        "candidate_file_count_total": len(candidates),
        "candidate_files_tied_to_orchestration": len(tied_candidates),
        "journal_hits": journal_hits[:100],
        "artifact_hits": artifact_hits[:100],
        "candidates_tied_to_orchestration": tied_candidates[:100],
        "all_candidate_summary": candidates[:100],
        "materialization_report": materialization,
        "evidence_summary": {
            "candidate_count": evidence.get("candidate_count", 0),
            "sector_count": evidence.get("sector_count", 0),
            "business_model_count": evidence.get("business_model_count", 0),
            "qualified_count": (evidence.get("ranking") or {}).get("qualified_count", 0),
        },
    }

    report["diagnosis"] = diagnose(report)
    save(TRACE_REPORT, report)
    return report

def diagnose(report: dict) -> dict:
    j = int(report.get("journal_hit_count", 0) or 0)
    a = int(report.get("artifact_hit_count", 0) or 0)
    c = int(report.get("candidate_files_tied_to_orchestration", 0) or 0)

    if c > 0:
        return {
            "status": "research_to_candidate_bridge_working",
            "next_action": "rerun_evidence_and_expand_if_diversity_targets_not_met",
        }
    if j > 0 or a > 0:
        return {
            "status": "research_output_exists_but_not_materialized",
            "next_action": "run_candidate_materialization_then_recheck",
        }
    return {
        "status": "orchestration_completed_without_traceable_output",
        "next_action": "dispatch_targeted_output_recovery_for_this_orchestration",
    }
