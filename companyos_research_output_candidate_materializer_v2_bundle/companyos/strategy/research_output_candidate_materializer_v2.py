from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
RAW_DIR = RUNTIME / "canonical_research_outputs"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
STATE = RUNTIME / "research_output_candidate_materializer_v2_state.json"
REPORT = RUNTIME / "research_output_candidate_materializer_v2_report.json"

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
    "description": ["description", "summary", "thesis", "concept", "details"],
    "evidence_sources": ["evidence_sources", "sources", "citations", "evidence"],
    "assumptions": ["assumptions", "key_assumptions"],
    "unknowns": ["unknowns", "gaps", "open_questions"],
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
    "evidence_uncertainty": 80.0,
}

def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj: Any):
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
    return s[:90] or "candidate"

def fp(c: dict) -> str:
    raw = "|".join([
        str(c.get("name", "")).strip().lower(),
        str(c.get("sector", "")).strip().lower(),
        str(c.get("business_model", "")).strip().lower(),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def candidate_from_mapping(d: dict, oid: str | None, source: str, low_confidence_text: bool=False) -> dict | None:
    name = first(d, ALIASES["name"])
    if not name:
        return None

    out = {
        "name": str(name),
        "sector": str(first(d, ALIASES["sector"]) or "unknown"),
        "business_model": str(first(d, ALIASES["business_model"]) or "unknown"),
        "description": str(first(d, ALIASES["description"]) or ""),
        "evidence_sources": first(d, ALIASES["evidence_sources"]) or [],
        "assumptions": first(d, ALIASES["assumptions"]) or [],
        "unknowns": first(d, ALIASES["unknowns"]) or [],
        "orchestration_id": oid,
        "materialized_from": source,
        "materialized_at_unix": time.time(),
    }

    supplied = 0
    for field in NUMERIC_FIELDS:
        aliases = ALIASES.get(field, [field])
        val = None
        for k in aliases:
            if k in d:
                val = num(d.get(k))
                if val is not None:
                    break
        if val is not None:
            out[field] = val
            supplied += 1

    estimated = []
    for field, default in DEFAULTS.items():
        if field not in out:
            out[field] = default
            estimated.append(field)

    if "evidence_confidence" not in out:
        base = 12.0 if low_confidence_text else 22.0
        out["evidence_confidence"] = min(55.0, base + supplied * 4.0)
        estimated.append("evidence_confidence")

    if low_confidence_text:
        out["evidence_uncertainty"] = max(float(out.get("evidence_uncertainty", 80) or 80), 85.0)

    out["estimated_fields"] = sorted(set(estimated))
    out["needs_enrichment"] = True
    out["candidate_fingerprint"] = fp(out)
    return out

def parse_json_blobs(text: str) -> list[dict]:
    found = []
    decoder = json.JSONDecoder()
    i = 0
    while i < len(text):
        j = text.find("{", i)
        if j < 0:
            break
        try:
            obj, end = decoder.raw_decode(text[j:])
            if isinstance(obj, dict):
                found.append(obj)
            i = j + end
        except Exception:
            i = j + 1
    return found

def parse_candidate_sections(text: str) -> list[dict]:
    found = []

    # Explicit JSON first.
    found.extend(parse_json_blobs(text))

    # Markdown-like candidate blocks.
    lines = text.splitlines()
    current = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # Heading styles: "1. Foo", "Candidate: Foo", "Opportunity: Foo"
        m = re.match(r'^(?:\d+[\.\)]\s*|candidate\s*[:\-]\s*|opportunity\s*[:\-]\s*)(.{3,140})$', line, flags=re.I)
        if m:
            if current and current.get("name"):
                found.append(current)
            current = {"name": m.group(1).strip()}
            continue

        if current is None:
            continue

        kv = re.match(r'^([A-Za-z_ /-]{2,50})\s*[:\-]\s*(.+)$', line)
        if not kv:
            # append prose to description
            current["description"] = (current.get("description","") + " " + line).strip()
            continue

        key = kv.group(1).strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")
        value = kv.group(2).strip()

        aliases = {
            "sector": "sector",
            "industry": "sector",
            "business_model": "business_model",
            "model": "business_model",
            "description": "description",
            "summary": "description",
            "market_demand": "market_demand",
            "demand": "market_demand",
            "expected_profit": "expected_profit",
            "profit_potential": "expected_profit",
            "probability_of_success": "probability_of_success",
            "margin": "margin",
            "recurring_revenue": "recurring_revenue",
            "scalability": "scalability",
            "capital_efficiency": "capital_efficiency",
            "speed_to_revenue": "speed_to_revenue",
            "automation_potential": "automation_potential",
            "defensibility": "defensibility",
            "competition": "competition",
            "customer_acquisition_difficulty": "customer_acquisition_difficulty",
            "regulatory_operational_risk": "regulatory_operational_risk",
            "capital_intensity": "capital_intensity",
            "evidence_uncertainty": "evidence_uncertainty",
            "evidence_confidence": "evidence_confidence",
        }
        if key in aliases:
            current[aliases[key]] = value
        else:
            current["description"] = (current.get("description","") + f" {kv.group(1)}: {value}").strip()

    if current and current.get("name"):
        found.append(current)

    return found

def walk(obj: Any, oid: str | None, source: str, out: list[dict]):
    if isinstance(obj, dict):
        c = candidate_from_mapping(obj, oid, source, low_confidence_text=False)
        if c:
            out.append(c)

        for v in obj.values():
            if isinstance(v, str) and len(v) > 80:
                for parsed in parse_candidate_sections(v):
                    c2 = candidate_from_mapping(parsed, oid, source, low_confidence_text=True)
                    if c2:
                        out.append(c2)
            else:
                walk(v, oid, source, out)

    elif isinstance(obj, list):
        for v in obj:
            walk(v, oid, source, out)

def process_capture_file(path: Path) -> list[dict]:
    obj = load(path, {})
    oid = obj.get("orchestration_id")
    source = str(path.relative_to(ROOT))
    out = []

    # Entire capture envelope, including goal/result/returns.
    walk(obj, oid, source, out)

    # The captured goal often contains research instructions + current candidate context.
    goal = obj.get("goal")
    if isinstance(goal, str):
        for parsed in parse_candidate_sections(goal):
            c = candidate_from_mapping(parsed, oid, source, low_confidence_text=True)
            if c:
                out.append(c)

    return out

def dedupe(items: list[dict]) -> list[dict]:
    best = {}
    for c in items:
        key = c["candidate_fingerprint"]
        old = best.get(key)
        if old is None:
            best[key] = c
            continue
        rank_old = (
            float(old.get("evidence_confidence", 0) or 0),
            len(old.get("evidence_sources", []) or []),
            -len(old.get("estimated_fields", []) or []),
        )
        rank_new = (
            float(c.get("evidence_confidence", 0) or 0),
            len(c.get("evidence_sources", []) or []),
            -len(c.get("estimated_fields", []) or []),
        )
        if rank_new > rank_old:
            best[key] = c
    return list(best.values())

def materialize_all() -> dict:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(RAW_DIR.glob("*.json")) if RAW_DIR.exists() else []

    found = []
    for p in raw_files[-300:]:
        found.extend(process_capture_file(p))

    found = dedupe(found)

    written = []
    repaired = 0
    for c in found:
        path = CANDIDATE_DIR / f"{slug(c['name'])}_{c['candidate_fingerprint']}.json"
        existing = load(path, {})

        if existing and isinstance(existing, dict):
            # Repair lineage and preserve richer existing data.
            changed = False
            oid = c.get("orchestration_id")
            existing.setdefault("source_orchestration_ids", [])
            if oid and oid not in existing["source_orchestration_ids"]:
                existing["source_orchestration_ids"].append(oid)
                changed = True
            if oid and not existing.get("orchestration_id"):
                existing["orchestration_id"] = oid
                changed = True
            if changed:
                existing["lineage_repaired_at_unix"] = time.time()
                save(path, existing)
                repaired += 1
                written.append(str(path.relative_to(ROOT)))
            continue

        c.setdefault("source_orchestration_ids", [])
        if c.get("orchestration_id") and c["orchestration_id"] not in c["source_orchestration_ids"]:
            c["source_orchestration_ids"].append(c["orchestration_id"])
        save(path, c)
        written.append(str(path.relative_to(ROOT)))

    report = {
        "generated_at_unix": time.time(),
        "raw_capture_file_count": len(raw_files),
        "candidate_objects_found": len(found),
        "candidate_files_written_or_repaired": len(written),
        "lineage_repairs": repaired,
        "written": written[:300],
    }
    save(REPORT, report)

    st = load(STATE, {"runs": []})
    st["last_run_unix"] = report["generated_at_unix"]
    st["last_result"] = report
    st.setdefault("runs", []).append(report)
    st["runs"] = st["runs"][-50:]
    save(STATE, st)

    return report
