from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = Path.home() / ".companyos_runtime"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
STATE_PATH = RUNTIME / "candidate_materialization_bridge_state.json"
REPORT_PATH = RUNTIME / "candidate_materialization_report.json"
RESEARCH_STATE = RUNTIME / "profit_first_research_pipeline_state.json"

JOURNAL_CANDIDATES = [
    RUNTIME / "full_autonomy_journal.jsonl",
    RUNTIME / "ceo_orchestration_journal.jsonl",
    RUNTIME / "canonical_production" / "journal.jsonl",
    ROOT / "companyos_runtime" / "full_autonomy_journal.jsonl",
    ROOT / ".companyos_runtime" / "full_autonomy_journal.jsonl",
    ROOT / "companyos_runtime" / "ceo_orchestration_journal.jsonl",
    ROOT / ".companyos_runtime" / "ceo_orchestration_journal.jsonl",
    ROOT / "companyos_runtime" / "canonical_production" / "journal.jsonl",
    ROOT / ".companyos_runtime" / "canonical_production" / "journal.jsonl",
]

SEARCH_ROOTS = [
    ROOT / "workspace",
    ROOT / "artifacts",
    ROOT / "exports",
    ROOT / "companyos_runtime",
    ROOT / ".companyos_runtime",
    RUNTIME,
]

NUMERIC_FIELDS = [
    "market_demand",
    "expected_profit",
    "probability_of_success",
    "margin",
    "recurring_revenue",
    "scalability",
    "capital_efficiency",
    "speed_to_revenue",
    "automation_potential",
    "defensibility",
    "competition",
    "customer_acquisition_difficulty",
    "regulatory_operational_risk",
    "capital_intensity",
    "evidence_uncertainty",
    "evidence_confidence",
]

ALIASES = {
    "name": ["name", "title", "venture", "opportunity", "idea", "business_name", "product_name"],
    "sector": ["sector", "industry", "market", "vertical"],
    "business_model": ["business_model", "model", "revenue_model", "business_type"],
    "description": ["description", "summary", "thesis", "concept"],
    "market_demand": ["market_demand", "demand", "demand_score", "market_score"],
    "expected_profit": ["expected_profit", "profit_potential", "profit_score", "profitability"],
    "probability_of_success": ["probability_of_success", "success_probability", "success_score"],
    "margin": ["margin", "gross_margin", "net_margin", "margin_score"],
    "recurring_revenue": ["recurring_revenue", "recurring_revenue_quality", "rr_score"],
    "scalability": ["scalability", "scale_score"],
    "capital_efficiency": ["capital_efficiency", "roi", "roi_score"],
    "speed_to_revenue": ["speed_to_revenue", "time_to_revenue_score"],
    "automation_potential": ["automation_potential", "automation_score"],
    "defensibility": ["defensibility", "moat", "moat_score"],
    "competition": ["competition", "competition_score"],
    "customer_acquisition_difficulty": ["customer_acquisition_difficulty", "cac_difficulty", "cac_score"],
    "regulatory_operational_risk": ["regulatory_operational_risk", "operational_risk", "risk_score"],
    "capital_intensity": ["capital_intensity", "startup_cost_score", "capital_required_score"],
    "evidence_uncertainty": ["evidence_uncertainty", "uncertainty"],
    "evidence_confidence": ["evidence_confidence", "confidence", "confidence_score"],
    "evidence_sources": ["evidence_sources", "sources", "citations", "evidence"],
    "assumptions": ["assumptions", "key_assumptions"],
    "unknowns": ["unknowns", "gaps", "open_questions"],
}


def _portable_path(path: Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)

def load_json(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def first(d: dict, names: list[str]):
    for k in names:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return None

def clamp_score(v: Any) -> float | None:
    try:
        if isinstance(v, str):
            txt = v.strip().replace("%", "")
            if not txt:
                return None
            v = float(txt)
        n = float(v)
        if 0 <= n <= 1:
            n *= 100
        return round(max(0.0, min(100.0, n)), 3)
    except Exception:
        return None

def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower()).strip("_")
    return s[:80] or "candidate"

def fingerprint(candidate: dict) -> str:
    raw = "|".join([
        str(candidate.get("name", "")).strip().lower(),
        str(candidate.get("sector", "")).strip().lower(),
        str(candidate.get("business_model", "")).strip().lower(),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def looks_like_candidate(d: dict) -> bool:
    name = first(d, ALIASES["name"])
    if not name:
        return False
    economics = 0
    for field in NUMERIC_FIELDS:
        if clamp_score(first(d, ALIASES.get(field, [field]))) is not None:
            economics += 1
    has_context = bool(first(d, ALIASES["sector"]) or first(d, ALIASES["business_model"]) or first(d, ALIASES["description"]))
    return has_context and economics >= 2

def normalize_candidate(d: dict, source: str, orchestration_id: str | None = None) -> dict | None:
    if not looks_like_candidate(d):
        return None

    out: dict[str, Any] = {
        "name": str(first(d, ALIASES["name"])),
        "sector": str(first(d, ALIASES["sector"]) or "unknown"),
        "business_model": str(first(d, ALIASES["business_model"]) or "unknown"),
        "description": str(first(d, ALIASES["description"]) or ""),
        "evidence_sources": first(d, ALIASES["evidence_sources"]) or [],
        "assumptions": first(d, ALIASES["assumptions"]) or [],
        "unknowns": first(d, ALIASES["unknowns"]) or [],
        "materialized_from": source,
        "orchestration_id": orchestration_id,
        "materialized_at_unix": time.time(),
    }

    populated = 0
    for field in NUMERIC_FIELDS:
        n = clamp_score(first(d, ALIASES.get(field, [field])))
        if n is not None:
            out[field] = n
            populated += 1

    # Conservative defaults only when absent; they are explicitly marked as estimates.
    defaults = {
        "market_demand": 50.0,
        "expected_profit": 50.0,
        "probability_of_success": 45.0,
        "margin": 50.0,
        "recurring_revenue": 35.0,
        "scalability": 50.0,
        "capital_efficiency": 50.0,
        "speed_to_revenue": 50.0,
        "automation_potential": 50.0,
        "defensibility": 35.0,
        "competition": 60.0,
        "customer_acquisition_difficulty": 60.0,
        "regulatory_operational_risk": 40.0,
        "capital_intensity": 50.0,
        "evidence_uncertainty": 70.0,
    }
    estimated_fields = []
    for k, v in defaults.items():
        if k not in out:
            out[k] = v
            estimated_fields.append(k)

    if "evidence_confidence" not in out:
        # Low confidence unless the research actually supplied many economics fields.
        out["evidence_confidence"] = min(60.0, 20.0 + populated * 4.0)
        estimated_fields.append("evidence_confidence")

    out["estimated_fields"] = estimated_fields
    out["needs_enrichment"] = bool(estimated_fields) or out["evidence_confidence"] < 55
    out["candidate_fingerprint"] = fingerprint(out)
    return out

def walk(obj: Any, source: str, orchestration_id: str | None, found: list[dict]):
    if isinstance(obj, dict):
        oid = (
            obj.get("orchestration_id")
            or obj.get("last_orchestration_id")
            or orchestration_id
        )
        c = normalize_candidate(obj, source, oid)
        if c:
            found.append(c)
        for v in obj.values():
            walk(v, source, oid, found)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, source, orchestration_id, found)

def read_jsonl(path: Path, max_lines: int = 3000) -> list[Any]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-max_lines:]
    except Exception:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out

def collect_recent_research_outputs() -> list[dict]:
    found: list[dict] = []

    # 1) Orchestration journals.
    for p in JOURNAL_CANDIDATES:
        if not p.exists():
            continue
        for obj in read_jsonl(p):
            walk(obj, _portable_path(p), None, found)

    # 2) JSON artifacts, excluding our already-materialized candidates/report files.
    scanned = 0
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.json"):
            if scanned >= 2500:
                break
            scanned += 1
            try:
                rel = _portable_path(p)
            except Exception:
                rel = str(p)
            if "profit_first_candidates/" in rel or rel.endswith("candidate_materialization_report.json"):
                continue
            obj = load_json(p, None)
            if obj is not None:
                walk(obj, rel, None, found)

    # Deduplicate by candidate identity.
    dedup: dict[str, dict] = {}
    for c in found:
        fp = c["candidate_fingerprint"]
        old = dedup.get(fp)
        if old is None or c.get("evidence_confidence", 0) > old.get("evidence_confidence", 0):
            dedup[fp] = c
    return list(dedup.values())

def materialize() -> dict:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    candidates = collect_recent_research_outputs()

    written = []
    for c in candidates:
        fn = f"{slug(c['name'])}_{c['candidate_fingerprint']}.json"
        path = CANDIDATE_DIR / fn
        existing = load_json(path, {})
        # Do not overwrite a richer candidate with a weaker extraction.
        if existing and float(existing.get("evidence_confidence", 0) or 0) > float(c.get("evidence_confidence", 0) or 0):
            continue
        save_json(path, c)
        written.append(_portable_path(path))

    report = {
        "generated_at_unix": time.time(),
        "candidates_extracted": len(candidates),
        "candidate_files_written_or_updated": len(written),
        "candidate_directory": _portable_path(CANDIDATE_DIR),
        "written": written[:200],
    }
    save_json(REPORT_PATH, report)

    st = load_json(STATE_PATH, {"runs": []})
    st["last_run_unix"] = report["generated_at_unix"]
    st["last_result"] = report
    st.setdefault("runs", []).append({
        "ts": report["generated_at_unix"],
        "candidates_extracted": len(candidates),
        "files_written": len(written),
    })
    st["runs"] = st["runs"][-100:]
    save_json(STATE_PATH, st)
    return report

def latest_research_orchestration_ids() -> list[str]:
    st = load_json(RESEARCH_STATE, {})
    ids = []
    for r in st.get("runs", [])[-20:]:
        oid = r.get("orchestration_id")
        if oid:
            ids.append(str(oid))
    return ids

def recovery_goal(orchestration_ids: list[str]) -> str:
    ids = ", ".join(orchestration_ids[-5:]) or "unknown"
    return f"""
RESEARCH OUTPUT RECOVERY

Recent profit-first market-scan orchestration IDs: {ids}

The prior research orchestration(s) completed without producing enough machine-readable candidate records.

Recover the substantive research already performed where possible, then produce structured JSON opportunity records under:
.companyos_runtime/profit_first_candidates/

Each candidate must include:
name, sector, business_model, description,
market_demand, expected_profit, probability_of_success, margin, recurring_revenue,
scalability, capital_efficiency, speed_to_revenue, automation_potential, defensibility,
competition, customer_acquisition_difficulty, regulatory_operational_risk,
capital_intensity, evidence_uncertainty, evidence_confidence,
evidence_sources, assumptions, unknowns.

Use 0-100 numeric fields. Do not invent certainty. Clearly separate estimates from evidence.
Do not create renamed/versioned duplicates.
Research/analysis only; preserve all existing approval, financial, external-action, credential,
signer, reconciliation, publication/deployment, legal, destructive, and irreversible-action gates.
""".strip()

def maybe_recover_missing_outputs(min_expected_candidates: int = 1, cooldown_seconds: int = 300) -> dict:
    existing = list(CANDIDATE_DIR.glob("*.json")) if CANDIDATE_DIR.exists() else []
    if len(existing) >= min_expected_candidates:
        return {"started": False, "reason": "candidate_outputs_exist", "count": len(existing)}

    state = load_json(STATE_PATH, {})
    last = float(state.get("last_recovery_unix", 0) or 0)
    if time.time() - last < cooldown_seconds:
        return {"started": False, "reason": "recovery_cooldown"}

    ids = latest_research_orchestration_ids()
    if not ids:
        return {"started": False, "reason": "no_recent_research_orchestrations"}

    try:
        from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
        rec = AutonomousCEOOrchestrator().start(
            goal=recovery_goal(ids),
            max_cycles=100,
            max_follow_up_depth=3,
            priority_base=248,
        )
        oid = getattr(rec, "orchestration_id", None)
        state["last_recovery_unix"] = time.time()
        state.setdefault("recovery_dispatches", []).append({
            "ts": state["last_recovery_unix"],
            "orchestration_id": oid,
            "source_research_orchestration_ids": ids[-5:],
        })
        state["recovery_dispatches"] = state["recovery_dispatches"][-50:]
        save_json(STATE_PATH, state)
        return {"started": True, "orchestration_id": oid, "source_ids": ids[-5:]}
    except Exception as exc:
        return {
            "started": False,
            "reason": "recovery_dispatch_failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
