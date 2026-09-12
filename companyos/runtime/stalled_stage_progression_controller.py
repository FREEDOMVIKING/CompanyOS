from __future__ import annotations
import json
import time
from pathlib import Path
from companyos.governance.venture_identity_resolver import canonical_id, display_name, is_internal

ROOT = Path.home() / "companyos"
IDENTITY = ROOT / ".companyos_runtime" / "venture_identity_progression.json"
STATE = ROOT / ".companyos_runtime" / "stalled_stage_progression_state.json"

STAGE_TASKS = {
    "VALIDATE": [
        "validate one specific customer problem, buyer, offer, price hypothesis, and measurable success criterion",
        "persist validation evidence and explicitly mark pass/fail",
        "if validation passes, advance immediately to the smallest sellable build instead of restarting broad research",
    ],
    "PACKAGE": [
        "package the tested release candidate",
        "create an export manifest and operator/deployment notes",
        "advance to launch-ready when packaging is complete",
    ],
    "LAUNCH": [
        "verify the deployed endpoint or customer-facing asset is reachable",
        "record deployment evidence and live URL where applicable",
        "advance to measurable customer acquisition using configured connectors and existing policy gates",
    ],
    "CUSTOMER_ACQUISITION": [
        "define one measurable acquisition experiment with channel, audience, offer, and success metric",
        "create internal campaign assets, messaging, landing copy, outreach templates, and a tracking plan",
        "prepare a lead/prospect list or channel plan using permitted research sources",
        "separate internally authorized work from external actions that still require approval",
        "after approved execution, record conversion, fulfillment status, customer feedback, and the next iteration",
    ],
    "LAUNCH_READY": [
        "prepare the launch checklist and authorized deployment path",
        "prepare customer-facing launch assets",
        "identify consequential external actions that still require approval",
    ],
    "BUILD": [
        "identify the smallest missing sellable feature",
        "implement or delegate that feature",
        "run an internal acceptance check and record results",
    ],
    "TEST": [
        "define explicit acceptance criteria",
        "run internal tests",
        "record failures and create only the fixes required to pass",
    ],
    "DISCOVER": [
        "define the customer problem and target segment",
        "collect evidence of demand",
        "produce a measurable opportunity brief",
    ],
}

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")

def canonical_ventures():
    src = load(IDENTITY, {"ventures": {}})
    merged = {}
    order = {
        "DISCOVER":0,"VALIDATE":1,"BUILD":2,"TEST":3,"PACKAGE":4,
        "LAUNCH_READY":5,"LAUNCH":6,"CUSTOMER_ACQUISITION":7,
        "OPERATE":8,"SCALE":9
    }

    for key, rec in (src.get("ventures") or {}).items():
        if not isinstance(rec, dict):
            continue
        cid = canonical_id(rec.get("canonical_id") or key)
        if not cid or is_internal(cid):
            continue

        cur = merged.setdefault(cid, {
            "canonical_id": cid,
            "display_name": display_name(cid),
            "aliases": set(),
            "artifact_count": 0,
            "stage": "DISCOVER",
            "unchanged_observations": 0,
        })

        for alias in rec.get("aliases", []) or []:
            cur["aliases"].add(alias)
        cur["aliases"].add(key)
        cur["artifact_count"] += int(rec.get("artifact_count", 0) or 0)
        cur["unchanged_observations"] = max(
            cur["unchanged_observations"],
            int(rec.get("unchanged_observations", 0) or 0)
        )

        stage = rec.get("stage", "DISCOVER")
        if order.get(stage, 0) > order.get(cur["stage"], 0):
            cur["stage"] = stage

    for row in merged.values():
        row["aliases"] = sorted(row["aliases"])
    return merged

def stalled_ventures(min_unchanged=3):
    rows = [
        row for row in canonical_ventures().values()
        if row["unchanged_observations"] >= min_unchanged
    ]
    rows.sort(key=lambda x: x["unchanged_observations"], reverse=True)
    return rows

def goal_for(row):
    stage = row.get("stage", "DISCOVER")
    tasks = STAGE_TASKS.get(
        stage,
        ["advance the venture to its next measurable lifecycle milestone"]
    )
    numbered = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
    return (
        f"Advance existing canonical CompanyOS venture '{row['canonical_id']}'.\n"
        f"Current stage: {stage}\n"
        f"Unchanged observations: {row['unchanged_observations']}\n"
        "Do not create a duplicate or version-suffixed venture. Reuse existing artifacts.\n"
        "Execute this INTERNAL and REVERSIBLE progression chain:\n"
        f"{numbered}\n"
        "Produce measurable state change. Keep consequential external actions, financial "
        "transactions, credential changes, destructive actions, and irreversible commitments "
        "behind existing approval and safety gates."
    )

def maybe_start(min_unchanged=3, cooldown_seconds=300):
    state = load(STATE, {"starts": [], "last_started_by_venture": {}})
    now = time.time()

    for row in stalled_ventures(min_unchanged):
        last = float(state["last_started_by_venture"].get(row["canonical_id"], 0) or 0)
        if now - last < cooldown_seconds:
            continue

        from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
        rec = AutonomousCEOOrchestrator().start(
            goal=goal_for(row),
            max_cycles=80,
            max_follow_up_depth=4,
            priority_base=190,
        )
        entry = {
            "ts": now,
            "canonical_id": row["canonical_id"],
            "stage": row["stage"],
            "orchestration_id": getattr(rec, "orchestration_id", None),
        }
        state["starts"].append(entry)
        state["starts"] = state["starts"][-200:]
        state["last_started_by_venture"][row["canonical_id"]] = now
        save(STATE, state)
        return {"started": True, "entry": entry}

    return {"started": False, "reason": "no_eligible_stalled_venture"}
