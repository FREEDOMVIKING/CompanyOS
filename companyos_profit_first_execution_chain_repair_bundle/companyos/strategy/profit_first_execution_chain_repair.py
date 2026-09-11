from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
STATE = RUNTIME / "profit_first_execution_chain_repair_state.json"
CANDIDATE_DIR = RUNTIME / "profit_first_candidates"
TRACE_REPORT = RUNTIME / "profit_first_orchestration_trace_report.json"

FANOUT_BATCHES = [
    {
        "name": "software_ai_data",
        "sectors": ["horizontal SaaS", "vertical SaaS", "AI automation", "developer tools", "data/API products"],
        "models": ["software_saas_ai", "data_api_licensing", "automation_products"],
    },
    {
        "name": "commerce_marketplaces",
        "sectors": ["e-commerce", "marketplaces", "consumer products", "B2B procurement"],
        "models": ["ecommerce_physical_products", "marketplaces_platforms"],
    },
    {
        "name": "media_digital",
        "sectors": ["digital products", "creator tools", "education", "content/media"],
        "models": ["digital_products", "content_media", "subscriptions_memberships"],
    },
    {
        "name": "leadgen_services",
        "sectors": ["lead generation", "professional services", "local services", "SMB operations"],
        "models": ["lead_generation_assets", "services", "automation_products"],
    },
    {
        "name": "apps_consumer",
        "sectors": ["mobile apps", "web apps", "consumer utilities", "productivity"],
        "models": ["mobile_web_apps", "subscriptions_memberships", "software_saas_ai"],
    },
    {
        "name": "licensing_b2b",
        "sectors": ["licensing", "compliance", "workflow software", "information products"],
        "models": ["data_api_licensing", "digital_products", "software_saas_ai"],
    },
    {
        "name": "nonconstruction_wildcards",
        "sectors": ["logistics tech", "hospitality tech", "health-adjacent admin", "finance operations", "real estate tech"],
        "models": ["software_saas_ai", "marketplaces_platforms", "automation_products"],
    },
]

def load(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def save(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def candidate_count() -> int:
    return len(list(CANDIDATE_DIR.glob("*.json"))) if CANDIDATE_DIR.exists() else 0

def latest_trace_status() -> dict:
    return load(TRACE_REPORT, {})

def batch_goal(batch: dict) -> str:
    return f"""
PROFIT-FIRST SPECIALIST MARKET RESEARCH BATCH

Batch: {batch['name']}
Focus sectors: {", ".join(batch['sectors'])}
Business-model families: {", ".join(batch['models'])}

MISSION
Produce at least 4 materially distinct venture candidates from this batch.
Do real comparative market/economic analysis before proposing candidates.

For EACH candidate, write one JSON file directly to:
.companyos_runtime/profit_first_candidates/

REQUIRED JSON FIELDS
name
sector
business_model
description
market_demand
expected_profit
probability_of_success
margin
recurring_revenue
scalability
capital_efficiency
speed_to_revenue
automation_potential
defensibility
competition
customer_acquisition_difficulty
regulatory_operational_risk
capital_intensity
evidence_uncertainty
evidence_confidence
evidence_sources
assumptions
unknowns
research_batch

RULES
- Numeric scores are 0-100.
- research_batch must equal "{batch['name']}".
- Do not create renamed/versioned variants of existing ventures.
- Do not default back to construction/contractor concepts unless uniquely justified by evidence.
- Separate facts, estimates, assumptions, and unknowns.
- Lower evidence_confidence when evidence is weak.
- Persist the candidate JSON files as an explicit completion requirement.
- Also write a batch summary to:
  .companyos_runtime/profit_first_research_batches/{batch['name']}_summary.json

This is research/analysis only.
Preserve all existing approval, spending, financial transaction, credential, signer,
reconciliation, publication/deployment, legal, destructive, and irreversible-action gates.
""".strip()

def dispatch_batch(batch: dict) -> dict:
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    rec = AutonomousCEOOrchestrator().start(
        goal=batch_goal(batch),
        max_cycles=100,
        max_follow_up_depth=3,
        priority_base=255,
    )
    return {
        "batch": batch["name"],
        "orchestration_id": getattr(rec, "orchestration_id", None),
        "ts": time.time(),
    }

def run_fanout(force: bool = False, max_batches: int = 7) -> dict:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "profit_first_research_batches").mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    st = load(STATE, {"runs": [], "dispatched_batches": {}})
    before = candidate_count()

    if before >= 20 and not force:
        return {
            "started": False,
            "reason": "candidate_target_already_met",
            "candidate_count": before,
        }

    dispatched = []
    for batch in FANOUT_BATCHES[:max_batches]:
        name = batch["name"]
        # Don't keep spamming the same batch unless forced.
        if name in st.get("dispatched_batches", {}) and not force:
            continue
        try:
            entry = dispatch_batch(batch)
            dispatched.append(entry)
            st.setdefault("dispatched_batches", {})[name] = entry
        except Exception as exc:
            dispatched.append({
                "batch": name,
                "error": f"{type(exc).__name__}: {exc}",
                "ts": time.time(),
            })

    run = {
        "ts": time.time(),
        "candidate_count_before": before,
        "dispatched": dispatched,
        "trace_status": (latest_trace_status().get("diagnosis") or {}).get("status"),
    }
    st.setdefault("runs", []).append(run)
    st["runs"] = st["runs"][-50:]
    st["last_run"] = run
    save(STATE, st)

    return {
        "started": bool(dispatched),
        "candidate_count_before": before,
        "batches_dispatched": len(dispatched),
        "dispatches": dispatched,
    }

def reset_dispatch_memory() -> dict:
    st = load(STATE, {})
    st["dispatched_batches"] = {}
    save(STATE, st)
    return {"reset": True}
