from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
TRACE_REPORT = RUNTIME / "profit_first_orchestration_trace_report.json"
STATE = RUNTIME / "orchestration_candidate_extractor_v2_state.json"
REPORT = RUNTIME / "orchestration_candidate_extractor_v2_report.json"

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

NAME_KEYS = ["name", "title", "venture", "opportunity", "idea", "business_name", "product_name"]
SECTOR_KEYS = ["sector", "industry", "market", "vertical"]
MODEL_KEYS = ["business_model", "model", "revenue_model", "business_type"]
DESC_KEYS = ["description", "summary", "thesis", "concept", "details"]

SCORE_ALIASES = {
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
}

DEFAULTS = {
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
    "evidence_uncertainty": 75.0,
}

def load_json(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def first(d: dict, keys: list[str]):
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return None

def num(v: Any) -> float | None:
    try:
        if isinstance(v, str):
            s = v.strip().replace("%", "")
            if not s:
                return None
            v = float(s)
        n = float(v)
        if 0 <= n <= 1:
            n *= 100
        return round(max(0.0, min(100.0, n)), 3)
    except Exception:
        return None

def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.strip().lower()).strip("_")
    return s[:80] or "candidate"

def fingerprint(c: dict) -> str:
    raw = "|".join([
        str(c.get("name", "")).strip().lower(),
        str(c.get("sector", "")).strip().lower(),
        str(c.get("business_model", "")).strip().lower(),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def latest_traced_orchestration_id() -> str | None:
    tr = load_json(TRACE_REPORT, {})
    oid = tr.get("orchestration_id")
    return str(oid) if oid else None

def flatten_text(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)

def parse_candidate_blocks_from_text(text: str) -> list[dict]:
    found = []

    # Try JSON objects embedded in prose/code fences.
    for block in re.findall(r'\{[\s\S]{80,5000}?\}', text):
        try:
            obj = json.loads(block)
            if isinstance(obj, dict):
                found.append(obj)
        except Exception:
            continue

    # Also support numbered opportunity prose like:
    # "1. Name - sector - model - description"
    lines = [x.strip(" -*\t") for x in text.splitlines() if x.strip()]
    for line in lines:
        m = re.match(r'^\d+[\.\)]\s*([^:|-]{3,120})\s*[:|-]\s*(.+)$', line)
        if not m:
            continue
        name = m.group(1).strip()
        desc = m.group(2).strip()
        if len(name) < 3 or len(desc) < 10:
            continue
        found.append({
            "name": name,
            "description": desc,
            "sector": "unknown",
            "business_model": "unknown",
        })
    return found

def candidate_from_dict(d: dict, oid: str, source: str, extracted_from_text=False) -> dict | None:
    name = first(d, NAME_KEYS)
    if not name:
        return None

    sector = first(d, SECTOR_KEYS) or "unknown"
    model = first(d, MODEL_KEYS) or "unknown"
    desc = first(d, DESC_KEYS) or ""

    candidate = {
        "name": str(name),
        "sector": str(sector),
        "business_model": str(model),
        "description": str(desc),
        "orchestration_id": oid,
        "materialized_from": source,
        "materialized_at_unix": time.time(),
        "evidence_sources": d.get("evidence_sources") or d.get("sources") or [],
        "assumptions": d.get("assumptions") or [],
        "unknowns": d.get("unknowns") or [],
        "extracted_from_text": bool(extracted_from_text),
    }

    supplied = 0
    estimated_fields = []
    for field, aliases in SCORE_ALIASES.items():
        val = None
        for k in aliases:
            if k in d:
                val = num(d.get(k))
                if val is not None:
                    break
        if val is not None:
            candidate[field] = val
            supplied += 1

    for field, default in DEFAULTS.items():
        if field not in candidate:
            candidate[field] = default
            estimated_fields.append(field)

    if "evidence_confidence" not in candidate:
        # Text extraction is useful for candidate identity, not strong evidence.
        base = 18.0 if extracted_from_text else 24.0
        candidate["evidence_confidence"] = min(55.0, base + supplied * 4.0)
        estimated_fields.append("evidence_confidence")

    if extracted_from_text:
        candidate["evidence_uncertainty"] = max(candidate.get("evidence_uncertainty", 75.0), 80.0)

    candidate["estimated_fields"] = sorted(set(estimated_fields))
    candidate["needs_enrichment"] = True
    candidate["candidate_fingerprint"] = fingerprint(candidate)
    return candidate

def walk_for_oid(obj: Any, oid: str, source: str, out: list[dict]):
    if isinstance(obj, dict):
        txt = flatten_text(obj)
        if oid in txt:
            c = candidate_from_dict(obj, oid, source, extracted_from_text=False)
            if c:
                out.append(c)

            # Search nested strings for candidate-like research output.
            for v in obj.values():
                if isinstance(v, str) and len(v) > 50:
                    for pd in parse_candidate_blocks_from_text(v):
                        c2 = candidate_from_dict(pd, oid, source, extracted_from_text=True)
                        if c2:
                            out.append(c2)

        for v in obj.values():
            walk_for_oid(v, oid, source, out)

    elif isinstance(obj, list):
        for v in obj:
            walk_for_oid(v, oid, source, out)

def scan_journals(oid: str, out: list[dict]):
    for p in JOURNALS:
        if not p.exists():
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()[-6000:]
        except Exception:
            continue
        for line in lines:
            if oid not in line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                obj = {"raw": line}
            walk_for_oid(obj, oid, str(p.relative_to(ROOT)), out)

            # Raw line may contain serialized JSON/prose output.
            for pd in parse_candidate_blocks_from_text(line):
                c = candidate_from_dict(pd, oid, str(p.relative_to(ROOT)), extracted_from_text=True)
                if c:
                    out.append(c)

def scan_artifacts(oid: str, out: list[dict]):
    scanned = 0
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if scanned >= 4000:
                return
            if not p.is_file():
                continue
            scanned += 1
            try:
                rel = str(p.relative_to(ROOT))
            except Exception:
                rel = str(p)

            if "profit_first_candidates/" in rel:
                continue
            if p.suffix.lower() == ".json":
                obj = load_json(p, None)
                if obj is not None:
                    walk_for_oid(obj, oid, rel, out)
            elif p.suffix.lower() in {".txt", ".md", ".log", ".jsonl"}:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if oid not in text:
                    continue
                for pd in parse_candidate_blocks_from_text(text):
                    c = candidate_from_dict(pd, oid, rel, extracted_from_text=True)
                    if c:
                        out.append(c)

def dedupe(candidates: list[dict]) -> list[dict]:
    by_fp: dict[str, dict] = {}
    for c in candidates:
        fp = c["candidate_fingerprint"]
        old = by_fp.get(fp)
        if old is None:
            by_fp[fp] = c
            continue

        # Prefer richer/non-text extraction and higher confidence.
        old_rank = (
            not old.get("extracted_from_text", False),
            float(old.get("evidence_confidence", 0) or 0),
            len(old.get("evidence_sources", []) or []),
        )
        new_rank = (
            not c.get("extracted_from_text", False),
            float(c.get("evidence_confidence", 0) or 0),
            len(c.get("evidence_sources", []) or []),
        )
        if new_rank > old_rank:
            by_fp[fp] = c
    return list(by_fp.values())

def extract_for_orchestration(oid: str | None = None) -> dict:
    oid = oid or latest_traced_orchestration_id()
    if not oid:
        report = {"ok": False, "reason": "no_traced_orchestration_id"}
        save_json(REPORT, report)
        return report

    raw: list[dict] = []
    scan_journals(oid, raw)
    scan_artifacts(oid, raw)
    candidates = dedupe(raw)

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for c in candidates:
        fn = f"{slug(c['name'])}_{c['candidate_fingerprint']}.json"
        path = CANDIDATE_DIR / fn
        existing = load_json(path, {})

        # Always stamp this orchestration ID on candidates extracted from this run.
        if existing and isinstance(existing, dict):
            # Preserve richer evidence but ensure lineage is repaired.
            if float(existing.get("evidence_confidence", 0) or 0) > float(c.get("evidence_confidence", 0) or 0):
                existing["orchestration_id"] = oid
                existing["lineage_repaired_at_unix"] = time.time()
                existing.setdefault("source_orchestration_ids", [])
                if oid not in existing["source_orchestration_ids"]:
                    existing["source_orchestration_ids"].append(oid)
                save_json(path, existing)
                written.append(str(path.relative_to(ROOT)))
                continue

        c.setdefault("source_orchestration_ids", [])
        if oid not in c["source_orchestration_ids"]:
            c["source_orchestration_ids"].append(oid)
        save_json(path, c)
        written.append(str(path.relative_to(ROOT)))

    report = {
        "ok": True,
        "generated_at_unix": time.time(),
        "orchestration_id": oid,
        "raw_candidate_objects_found": len(raw),
        "deduplicated_candidates_found": len(candidates),
        "candidate_files_written_or_repaired": len(written),
        "written": written[:200],
    }
    save_json(REPORT, report)

    st = load_json(STATE, {"runs": []})
    st["last_run_unix"] = report["generated_at_unix"]
    st["last_orchestration_id"] = oid
    st["last_result"] = report
    st.setdefault("runs", []).append(report)
    st["runs"] = st["runs"][-50:]
    save_json(STATE, st)
    return report
