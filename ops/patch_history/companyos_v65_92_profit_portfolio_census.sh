#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V65.92 PROFIT PORTFOLIO CENSUS ====="
echo "ACTION=READ_ONLY_PORTFOLIO_AUDIT"
echo "WRITES=REPORT_ONLY"
echo "FINANCIAL_ACTIONS=DISABLED"
echo "EXTERNAL_ACTIONS=DISABLED"

python - <<'PY'
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from collections import Counter, defaultdict
import json
import re
import time

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
REPORT_DIR = Path.home() / ".companyos_runtime" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def load(path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(Path(path).read_text(errors="ignore"))
    except Exception:
        return default

def slug(v):
    return re.sub(r"[^a-z0-9]+", "-", str(v or "").lower()).strip("-")[:80]

def norm_text(v):
    return " ".join(str(v or "").lower().split())

# Use the live profit engine's own discovery + scoring contract so this census
# matches what CompanyOS currently considers a commercial opportunity.
from companyos.runtime import profit_opportunity_engine as poe

rows = poe.discover()

# Current strict qualification reasons.
qual_fn = getattr(poe, "_candidate_qualification_reasons", None)

def qualification(o):
    if callable(qual_fn):
        return list(qual_fn(o))
    reasons = []
    if getattr(o, "score", 0) < 45:
        reasons.append("score_below_execution_threshold")
    if getattr(o, "evidence_count", 0) < 1:
        reasons.append("missing_external_evidence")
    if getattr(o, "probability", 0) <= 0:
        reasons.append("probability_unestimated")
    if getattr(o, "expected_profit", 0) <= 0:
        reasons.append("profit_unestimated")
    if not str(getattr(o, "next_action", "") or "").strip():
        reasons.append("missing_executable_next_action")
    return reasons

# Dedupe again conservatively by name + mechanism + category so renamed files do
# not inflate the apparent number of distinct money-making ideas.
distinct = {}
for o in rows:
    key = (
        norm_text(getattr(o, "name", "")),
        norm_text(getattr(o, "mechanism", "")),
        norm_text(getattr(o, "category", "")),
    )
    prev = distinct.get(key)
    if prev is None or getattr(o, "score", 0) > getattr(prev, "score", 0):
        distinct[key] = o

ideas = sorted(
    distinct.values(),
    key=lambda o: (float(getattr(o, "score", 0)), float(getattr(o, "expected_profit", 0))),
    reverse=True,
)

# Inspect venture workspaces.
workspace_rows = []
workspace_by_slug = {}
workspace_root = ROOT / "workspace"
if workspace_root.exists():
    for brief in workspace_root.glob("*/venture_brief.json"):
        d = load(brief, {})
        if not isinstance(d, dict) or not d:
            continue
        rec = {
            "slug": brief.parent.name,
            "name": d.get("name"),
            "stage": d.get("stage"),
            "objective": d.get("objective"),
            "updated_at_unix": d.get("updated_at_unix"),
            "path": str(brief.parent),
        }
        workspace_rows.append(rec)
        workspace_by_slug[brief.parent.name] = rec

# Inspect dispatch history to determine which ideas have actually received
# independent execution orchestrations.
exec_state = load(RT / "profit_execution_state.json", {})
dispatches = exec_state.get("dispatches") or []
dispatch_by_slug = defaultdict(list)

for d in dispatches:
    if not isinstance(d, dict):
        continue
    s = slug(d.get("slug") or d.get("name"))
    if s:
        dispatch_by_slug[s].append(d)

# Inspect launch ledger. This is the strongest evidence of a separately
# published venture.
launches = []
ledger = RT / "venture_launch_ledger.jsonl"
if ledger.exists():
    for line in ledger.read_text(errors="ignore").splitlines():
        try:
            d = json.loads(line)
        except Exception:
            continue
        if isinstance(d, dict):
            launches.append(d)

# Include the current manually validated live site if it is represented only in
# the live validation artifact.
live_validation = load(RT / "live_validation_latest.json", {})
live_tracking = load(RT / "live_validation_tracking.json", {})

published_slugs = set()
published = []

for d in launches:
    s = slug(d.get("slug") or d.get("title") or d.get("name"))
    if not s:
        continue
    published_slugs.add(s)
    published.append({
        "slug": s,
        "name": d.get("title") or d.get("name"),
        "public_url": d.get("public_url"),
        "status": d.get("status"),
        "source": "venture_launch_ledger",
    })

for d, source in ((live_validation, "live_validation_latest"), (live_tracking, "live_validation_tracking")):
    if isinstance(d, dict) and d:
        name = d.get("candidate_name") or d.get("venture_title")
        url = d.get("stable_public_url") or d.get("public_url")
        if name or url:
            s = slug(name or "regional-construction-ai")
            if s not in published_slugs:
                published_slugs.add(s)
                published.append({
                    "slug": s,
                    "name": name,
                    "public_url": url,
                    "status": "live_validation",
                    "source": source,
                })

# Policy tells us how many simultaneous validation bets the architecture intends.
try:
    from companyos.strategy.profit_first_venture_engine import ensure_policy
    policy = ensure_policy()
except Exception:
    policy = {}

max_bets = int(policy.get("max_active_validation_bets", 3) or 3)

summary_rows = []
eligible = []
for rank, o in enumerate(ideas, start=1):
    reasons = qualification(o)
    s = slug(getattr(o, "name", ""))
    w = workspace_by_slug.get(s)
    dlist = dispatch_by_slug.get(s, [])
    is_published = s in published_slugs

    state = "candidate"
    if is_published:
        state = "published_validation"
    elif dlist:
        state = "execution_orchestration_started"
    elif w:
        state = "workspace_created"
    elif not reasons:
        state = "execution_qualified"
    else:
        state = "research_or_enrichment"

    rec = {
        "rank": rank,
        "id": getattr(o, "id", None),
        "name": getattr(o, "name", None),
        "business_model": getattr(o, "mechanism", None),
        "sector": getattr(o, "category", None),
        "score": getattr(o, "score", None),
        "expected_profit": getattr(o, "expected_profit", None),
        "margin": getattr(o, "margin", None),
        "probability": getattr(o, "probability", None),
        "evidence_count": getattr(o, "evidence_count", None),
        "evidence_quality": getattr(o, "evidence_quality", None),
        "readiness": getattr(o, "readiness", None),
        "time_to_cash_days": getattr(o, "time_to_cash_days", None),
        "capital_required": getattr(o, "capital_required", None),
        "next_action": getattr(o, "next_action", None),
        "qualification_blockers": reasons,
        "runtime_state": state,
        "workspace_present": bool(w),
        "execution_dispatch_count": len(dlist),
        "published": is_published,
        "source": getattr(o, "source", None),
    }
    summary_rows.append(rec)
    if not reasons:
        eligible.append(rec)

# Diversity diagnostics among top candidates.
sector_counts = Counter(str(x.get("sector") or "unknown").lower() for x in summary_rows[:20])
model_counts = Counter(str(x.get("business_model") or "unknown").lower() for x in summary_rows[:20])

active_internal = [
    x for x in summary_rows
    if x["runtime_state"] in ("execution_orchestration_started", "published_validation")
]
active_distinct = len({
    (norm_text(x["name"]), norm_text(x["business_model"]), norm_text(x["sector"]))
    for x in active_internal
})

available_parallel_slots = max(0, max_bets - active_distinct)

# Choose a suggested set for the next parallel-validation patch, with a mild
# diversity preference. This DOES NOT start anything.
suggested = []
seen_sectors = set()
seen_models = set()

for x in summary_rows:
    if len(suggested) >= max_bets:
        break
    # Prioritize already-qualified candidates.
    if x["qualification_blockers"]:
        continue
    sec = norm_text(x["sector"])
    model = norm_text(x["business_model"])
    if suggested and sec in seen_sectors and model in seen_models:
        continue
    suggested.append(x)
    seen_sectors.add(sec)
    seen_models.add(model)

# If strict qualification produces too few, include top research bets separately
# so we can see what should be enriched next, without pretending they are ready.
research_bets = []
for x in summary_rows:
    if len(research_bets) >= max_bets:
        break
    if x in suggested:
        continue
    research_bets.append(x)

report = {
    "version": "V65.92",
    "timestamp_unix": time.time(),
    "objective": "risk_adjusted_realized_profit",
    "distinct_money_making_ideas": len(summary_rows),
    "execution_qualified_ideas": len(eligible),
    "workspace_count": len(workspace_rows),
    "execution_dispatch_history_count": len(dispatches),
    "published_distinct_ventures": len(published_slugs),
    "published_ventures": published,
    "active_distinct_validation_or_execution_bets": active_distinct,
    "policy_max_active_validation_bets": max_bets,
    "available_parallel_slots": available_parallel_slots,
    "top20_sector_counts": dict(sector_counts),
    "top20_business_model_counts": dict(model_counts),
    "ideas": summary_rows,
    "strict_parallel_candidates": suggested,
    "top_research_bets_if_more_evidence_needed": research_bets,
    "mutation_performed": False,
}

report_path = REPORT_DIR / f"v65_92_profit_portfolio_census_{int(time.time())}.json"
report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

print("DISTINCT_MONEY_MAKING_IDEAS=", len(summary_rows))
print("EXECUTION_QUALIFIED_IDEAS=", len(eligible))
print("WORKSPACE_COUNT=", len(workspace_rows))
print("EXECUTION_DISPATCH_HISTORY_COUNT=", len(dispatches))
print("PUBLISHED_DISTINCT_VENTURES=", len(published_slugs))
print("ACTIVE_DISTINCT_VALIDATION_OR_EXECUTION_BETS=", active_distinct)
print("POLICY_MAX_ACTIVE_VALIDATION_BETS=", max_bets)
print("AVAILABLE_PARALLEL_SLOTS=", available_parallel_slots)
print("TOP20_SECTOR_COUNTS=", dict(sector_counts))
print("TOP20_BUSINESS_MODEL_COUNTS=", dict(model_counts))

print("\n===== PUBLISHED VENTURES =====")
for x in published:
    print(json.dumps(x, sort_keys=True, default=str))

print("\n===== TOP DISTINCT MONEY-MAKING IDEAS =====")
for x in summary_rows[:20]:
    compact = {
        "rank": x["rank"],
        "name": x["name"],
        "business_model": x["business_model"],
        "sector": x["sector"],
        "score": x["score"],
        "expected_profit": x["expected_profit"],
        "probability": x["probability"],
        "evidence_count": x["evidence_count"],
        "readiness": x["readiness"],
        "state": x["runtime_state"],
        "blockers": x["qualification_blockers"],
    }
    print(json.dumps(compact, sort_keys=True, default=str))

print("\n===== STRICT PARALLEL CANDIDATES =====")
for x in suggested:
    print(json.dumps({
        "rank": x["rank"],
        "name": x["name"],
        "business_model": x["business_model"],
        "sector": x["sector"],
        "score": x["score"],
        "state": x["runtime_state"],
    }, sort_keys=True, default=str))

print("\n===== TOP RESEARCH BETS IF QUALIFICATION IS TOO THIN =====")
for x in research_bets:
    print(json.dumps({
        "rank": x["rank"],
        "name": x["name"],
        "business_model": x["business_model"],
        "sector": x["sector"],
        "score": x["score"],
        "blockers": x["qualification_blockers"],
    }, sort_keys=True, default=str))

print("REPORT=", report_path)
print("V65_92_READ_ONLY=PASS")
print("V65_92_DISTINCT_IDEA_CENSUS=PASS")
print("V65_92_PARALLELISM_AUDIT=PASS")
print("V65_92_COMPLETE")
PY
