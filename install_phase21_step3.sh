#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 3 - Opportunity Activation Pipeline"
echo "============================================================"

cat > "$MEM/opportunity_activation_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_activation": true,
  "maximum_candidates": 10,
  "minimum_alignment_score": 50,
  "require_system_ready": true,
  "require_execution_eligibility": true,
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

cat > "$AGENTS/opportunity_activation_pipeline.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "opportunity_activation_config.json"
ALIGN = MEM / "strategic_alignment_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "opportunity_activation_state.json"
REPORT = MEM / "opportunity_activation_report.json"
HEALTH = MEM / "opportunity_activation_health.json"
QUEUE = MEM / "opportunity_activation_queue.json"

CATEGORY_MAP = {
    "internal": "internal_reversible",
    "analysis": "internal_read_only",
    "research": "external_read_only",
    "customer": "customer_contact",
    "sales": "external_write",
    "publication": "publication",
    "finance": "spending"
}

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

def normalize_category(value: Any) -> str:
    if not value:
        return "internal_read_only"
    key = str(value).strip().lower()
    return CATEGORY_MAP.get(key, key if key in {
        "internal_read_only",
        "internal_reversible",
        "external_read_only",
        "external_write",
        "customer_contact",
        "publication",
        "spending"
    } else "internal_read_only")

def activate() -> dict[str, Any]:
    cfg = load(CFG, {})
    align = load(ALIGN, {})
    eligibility = load(ELIGIBILITY, {})

    system_ready = eligibility.get("system_ready") is True
    matrix = eligibility.get("eligibility", {})

    minimum = float(cfg.get("minimum_alignment_score", 50))
    maximum = int(cfg.get("maximum_candidates", 10))

    candidates = []
    blocked = []

    for item in align.get("eligible_opportunities", [])[:maximum]:
        score = float(item.get("alignment_score", 0))
        category = normalize_category(item.get("category"))

        if score < minimum:
            blocked.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "reason": "below_minimum_alignment_score",
                "alignment_score": score
            })
            continue

        if cfg.get("require_system_ready", True) and not system_ready:
            blocked.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "reason": "system_not_ready",
                "alignment_score": score,
                "category": category
            })
            continue

        if cfg.get("require_execution_eligibility", True) and not bool(matrix.get(category, False)):
            blocked.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "reason": "category_not_eligible",
                "alignment_score": score,
                "category": category
            })
            continue

        candidates.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "category": category,
            "alignment_score": score,
            "status": "activated",
            "source": item.get("source"),
            "recommendation": item.get("recommendation")
        })

    queue = {
        "generated_at": now(),
        "system_ready": system_ready,
        "candidates": candidates
    }
    save(QUEUE, queue)

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "activated_count": len(candidates),
        "blocked_count": len(blocked),
        "activated": candidates,
        "blocked": blocked,
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
        "last_activation_at": now(),
        "system_ready": system_ready,
        "activated_count": len(candidates),
        "blocked_count": len(blocked),
        "top_candidate": candidates[0]["title"] if candidates else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "activated_count": len(candidates),
        "blocked_count": len(blocked)
    })

    return {
        "success": True,
        "status": "opportunity_activation_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_activation_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "queue": load(QUEUE, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "activate":
        result = activate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["activate", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/opportunity_activation_pipeline.py"

cat > "$CTL/opportunityactivatectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "opportunity_activation_pipeline.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/opportunityactivatectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_activation_pipeline.py" "$CTL/opportunityactivatectl"

echo "[2/6] Activating aligned opportunities..."
python "$CTL/opportunityactivatectl" activate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "opportunity-activation-pipeline",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/opportunityactivatectl", "activate"]
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

echo "[5/6] Checking activation status..."
python "$CTL/opportunityactivatectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "opportunity_activation_pipeline.py",
    root / "companyos" / "opportunityactivatectl",
    root / "ceo_memory" / "opportunity_activation_config.json",
    root / "ceo_memory" / "opportunity_activation_state.json",
    root / "ceo_memory" / "opportunity_activation_report.json",
    root / "ceo_memory" / "opportunity_activation_health.json",
    root / "ceo_memory" / "opportunity_activation_queue.json",
    root / "ceo_memory" / "autonomous_operations_config.json"
]

for path in required:
    if not path.exists() or path.stat().st_size <= 0:
        errors.append(f"Missing/empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

try:
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
        (x for x in sched.get("jobs", []) if x.get("id") == "opportunity-activation-pipeline"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Opportunity activation scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 21 Step 3 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 3 INSTALLED"
echo " OPPORTUNITY ACTIVATION PIPELINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/opportunityactivatectl activate"
echo "  python companyos/opportunityactivatectl status"
