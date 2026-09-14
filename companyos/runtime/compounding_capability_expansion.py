from __future__ import annotations
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
RT = ROOT / ".companyos_runtime"
FEEDBACK = RT / "capability_feedback"
EXPANSION = RT / "capability_expansion"
STATE = EXPANSION / "compounding_state.json"
QUEUE = EXPANSION / "next_capability_queue.json"
EVENTS = EXPANSION / "compounding_events.jsonl"

def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)

def _event(kind: str, data: Dict[str, Any]):
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a") as f:
        f.write(json.dumps({"ts": time.time(), "kind": kind, **data}, sort_keys=True) + "\n")

def _feedback_payload() -> Dict[str, Any]:
    candidates = [
        FEEDBACK / "state.json",
        FEEDBACK / "capability_feedback_state.json",
        RT / "capability_feedback_state.json",
    ]
    for p in candidates:
        x = _load(p, None)
        if isinstance(x, dict):
            return x
    # V7 control output commonly persists capability records elsewhere.
    for p in sorted(RT.rglob("*feedback*.json"), key=lambda q: q.stat().st_mtime if q.exists() else 0, reverse=True):
        x = _load(p, None)
        if isinstance(x, dict) and ("capabilities" in x or "summary" in x):
            return x
    return {}

def _records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = payload.get("capabilities", {})
    if isinstance(c, dict):
        return [dict(v, capability_id=k) if isinstance(v, dict) else {"capability_id": k}
                for k, v in c.items()]
    if isinstance(c, list):
        return [x for x in c if isinstance(x, dict)]
    return []

def _gap_for(rec: Dict[str, Any]) -> Dict[str, Any] | None:
    cid = str(rec.get("capability_id") or rec.get("id") or rec.get("name") or "unknown")
    status = str(rec.get("status", "")).lower()
    rel = float(rec.get("reliability", 0) or 0)
    utility = float(rec.get("utility_score", 0) or 0)
    uses = int(rec.get("uses_observed", rec.get("uses", 0)) or 0)
    failures = int(rec.get("failures", 0) or 0)

    if status == "quarantined" or failures >= 2:
        return {
            "source_capability": cid,
            "gap_type": "reliability_repair",
            "priority": 95,
            "reason": f"{cid} is failing or quarantined",
            "requested_capability": f"{cid}_reliability_analyzer",
        }
    if status == "active" and uses >= 3 and utility < 0.70:
        return {
            "source_capability": cid,
            "gap_type": "utility_improvement",
            "priority": 80,
            "reason": f"{cid} is reliable enough to use but has low observed utility",
            "requested_capability": f"{cid}_utility_optimizer",
        }
    if status == "active" and rel >= .80 and uses >= 3:
        # Successful capabilities should reveal the next bottleneck, not clone themselves.
        return {
            "source_capability": cid,
            "gap_type": "downstream_bottleneck_discovery",
            "priority": 65,
            "reason": f"{cid} is active and reliable; inspect its outputs for the next unresolved bottleneck",
            "requested_capability": f"{cid}_downstream_gap_detector",
        }
    return None

def once() -> Dict[str, Any]:
    payload = _feedback_payload()
    records = _records(payload)
    state = _load(STATE, {"seen": {}, "cycles": 0})
    seen = state.setdefault("seen", {})

    gaps = []
    for rec in records:
        g = _gap_for(rec)
        if not g:
            continue
        key = hashlib.sha256(
            (g["source_capability"] + "|" + g["gap_type"] + "|" + g["requested_capability"]).encode()
        ).hexdigest()[:20]
        g["gap_id"] = key
        if key not in seen:
            gaps.append(g)

    gaps.sort(key=lambda x: (-x["priority"], x["requested_capability"]))
    # One new capability request per cycle prevents runaway self-replication.
    selected = gaps[:1]

    queue = _load(QUEUE, {"requests": []})
    reqs = queue.setdefault("requests", [])
    existing = {x.get("gap_id") for x in reqs if isinstance(x, dict)}
    for g in selected:
        if g["gap_id"] not in existing:
            item = {
                **g,
                "created_at": time.time(),
                "status": "research_required",
                "execution_allowed": False,
                "external_action_allowed": False,
                "financial_action_allowed": False,
                "credential_access_allowed": False,
                "deployment_allowed": False,
                "generation_contract": {
                    "must_be_new_capability": True,
                    "must_have_tests": True,
                    "must_pass_isolated_validation": True,
                    "must_not_duplicate_source": True,
                    "promotion_requires_existing_expansion_pipeline": True,
                },
            }
            reqs.append(item)
            seen[g["gap_id"]] = {"created_at": item["created_at"], "status": item["status"]}
            _event("next_gap_queued", {"gap_id": g["gap_id"], "requested_capability": g["requested_capability"]})

    state["cycles"] = int(state.get("cycles", 0)) + 1
    state["last_cycle_unix"] = time.time()
    state["active_capabilities_seen"] = sum(1 for r in records if str(r.get("status","")).lower() == "active")
    state["records_seen"] = len(records)
    state["new_requests"] = len(selected)
    _write(QUEUE, queue)
    _write(STATE, state)
    return {"healthy": True, "state": state, "selected": selected, "queue_count": len(reqs)}

def run():
    interval = max(60, int(os.getenv("COMPANYOS_COMPOUNDING_INTERVAL_SECONDS", "300")))
    while True:
        try:
            once()
        except Exception as e:
            _event("cycle_error", {"error": repr(e)})
        time.sleep(interval)

if __name__ == "__main__":
    run()
