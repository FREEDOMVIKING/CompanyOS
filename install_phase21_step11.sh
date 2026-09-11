#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 11 - Opportunity Portfolio Allocation Engine"
echo "============================================================"

cat > "$MEM/opportunity_portfolio_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_allocation": true,
  "maximum_active_opportunities": 5,
  "minimum_final_score": 50,
  "diversify_by_category": true,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/opportunity_portfolio_allocator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "opportunity_portfolio_config.json"
RERANK = MEM / "opportunity_rerank_report.json"

STATE = MEM / "opportunity_portfolio_state.json"
REPORT = MEM / "opportunity_portfolio_report.json"
HEALTH = MEM / "opportunity_portfolio_health.json"
PORTFOLIO = MEM / "active_opportunity_portfolio.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def allocate() -> dict[str, Any]:
    cfg = load(CFG, {})
    rows = load(RERANK, {}).get("reranked_opportunities", [])

    maximum = int(cfg.get("maximum_active_opportunities", 5))
    minimum = float(cfg.get("minimum_final_score", 50))
    diversify = bool(cfg.get("diversify_by_category", True))

    eligible = []
    for row in rows:
        try:
            score = float(row.get("final_opportunity_score", 0))
        except Exception:
            score = 0.0

        if score >= minimum:
            eligible.append(row)

    eligible.sort(
        key=lambda x: float(x.get("final_opportunity_score", 0)),
        reverse=True
    )

    selected = []
    used_categories = set()

    if diversify:
        for row in eligible:
            category = row.get("category") or "uncategorized"
            if category in used_categories:
                continue
            selected.append(row)
            used_categories.add(category)
            if len(selected) >= maximum:
                break

    if len(selected) < maximum:
        selected_ids = {str(x.get("id")) for x in selected}
        for row in eligible:
            if str(row.get("id")) in selected_ids:
                continue
            selected.append(row)
            if len(selected) >= maximum:
                break

    active = []
    for index, row in enumerate(selected, start=1):
        active.append({
            "portfolio_rank": index,
            "id": row.get("id"),
            "title": row.get("title"),
            "category": row.get("category"),
            "final_opportunity_score": row.get("final_opportunity_score"),
            "learning_samples": row.get("learning_samples"),
            "learning_active": row.get("learning_active"),
            "status": "active_candidate"
        })

    payload = {
        "generated_at": now(),
        "active_count": len(active),
        "opportunities": active
    }
    save(PORTFOLIO, payload)

    report = {
        "generated_at": now(),
        "eligible_count": len(eligible),
        "selected_count": len(active),
        "active_portfolio": active,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_allocated_at": now(),
        "eligible_count": len(eligible),
        "selected_count": len(active),
        "top_opportunity": active[0]["title"] if active else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "selected_count": len(active)
    })

    return {
        "success": True,
        "status": "opportunity_portfolio_allocation_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_portfolio_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "portfolio": load(PORTFOLIO, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "allocate":
        result = allocate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["allocate", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/opportunity_portfolio_allocator.py"

cat > "$CTL/opportunityportfolioctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "opportunity_portfolio_allocator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/opportunityportfolioctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_portfolio_allocator.py" "$CTL/opportunityportfolioctl"

echo "[2/6] Allocating opportunity portfolio..."
python "$CTL/opportunityportfolioctl" allocate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "opportunity-portfolio-allocation",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/opportunityportfolioctl", "allocate"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)
if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print(json.dumps({"success": True, "job_id": job["id"]}, indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking portfolio status..."
python "$CTL/opportunityportfolioctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home()/"companyos"
errors = []

required = [
    root/"agents"/"opportunity_portfolio_allocator.py",
    root/"companyos"/"opportunityportfolioctl",
    root/"ceo_memory"/"opportunity_portfolio_config.json",
    root/"ceo_memory"/"opportunity_portfolio_state.json",
    root/"ceo_memory"/"opportunity_portfolio_report.json",
    root/"ceo_memory"/"opportunity_portfolio_health.json",
    root/"ceo_memory"/"active_opportunity_portfolio.json",
    root/"ceo_memory"/"autonomous_operations_config.json"
]

for p in required:
    if not p.exists() or p.stat().st_size <= 0:
        errors.append(f"Missing/empty: {p}")

for p in required[:2]:
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

cfg = json.loads(required[2].read_text())
for key in [
    "automatic_external_write",
    "automatic_customer_contact",
    "automatic_publication",
    "automatic_spending",
    "automatic_code_changes",
    "automatic_merge",
    "automatic_deploy",
    "automatic_destructive_actions"
]:
    if cfg.get(key) is not False:
        errors.append(f"{key} must remain disabled")

sched = json.loads(required[7].read_text())
job = next(
    (x for x in sched.get("jobs", [])
     if x.get("id") == "opportunity-portfolio-allocation"),
    None
)
if not job or job.get("enabled") is not True:
    errors.append("Opportunity portfolio scheduler job missing/disabled")

print("--------------------------------------------")
print("Phase 21 Step 11 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 11 INSTALLED"
echo " OPPORTUNITY PORTFOLIO ALLOCATION ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/opportunityportfolioctl allocate"
echo "  python companyos/opportunityportfolioctl status"
