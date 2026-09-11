#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 2 - Strategic Opportunity Alignment Engine"
echo "============================================================"

cat > "$MEM/strategic_alignment_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_alignment": true,
  "maximum_opportunities": 20,
  "goal_weight": 0.40,
  "priority_weight": 0.35,
  "forecast_weight": 0.25,
  "minimum_alignment_score": 50,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_git_reset": false,
  "automatic_git_clean": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/strategic_opportunity_alignment.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "strategic_alignment_config.json"
OPPS = MEM / "opportunity_discovery_results.json"
STRATEGY = MEM / "strategic_orchestrator_report.json"
PRIORITIES = MEM / "feedback_priority_report.json"
FORECAST = MEM / "business_forecasting_report.json"

STATE = MEM / "strategic_alignment_state.json"
REPORT = MEM / "strategic_alignment_report.json"
HEALTH = MEM / "strategic_alignment_health.json"

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

def clamp(v: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, v))

def normalize_opportunities(doc: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("opportunities", "results", "items"):
        value = doc.get(key)
        if isinstance(value, list):
            return value
    return []

def score_opportunity(
    opp: dict[str, Any],
    goal_signal: float,
    priority_signal: float,
    forecast_signal: float,
    cfg: dict[str, Any]
) -> float:
    raw = opp.get(
        "score",
        opp.get(
            "opportunity_score",
            opp.get("priority", 50)
        )
    )
    try:
        base = float(raw)
    except Exception:
        base = 50.0

    gw = float(cfg.get("goal_weight", 0.40))
    pw = float(cfg.get("priority_weight", 0.35))
    fw = float(cfg.get("forecast_weight", 0.25))
    total = gw + pw + fw
    if total <= 0:
        gw, pw, fw, total = 0.40, 0.35, 0.25, 1.0

    strategic = (
        goal_signal * gw +
        priority_signal * pw +
        forecast_signal * fw
    ) / total

    return clamp((base * 0.50) + (strategic * 0.50))

def align() -> dict[str, Any]:
    cfg = load(CFG, {})
    opp_doc = load(OPPS, {})
    strategy = load(STRATEGY, {})
    priority_doc = load(PRIORITIES, {})
    forecast = load(FORECAST, {})

    opportunities = normalize_opportunities(opp_doc)
    max_opps = int(cfg.get("maximum_opportunities", 20))
    minimum = float(cfg.get("minimum_alignment_score", 50))

    eligible_goals = strategy.get("eligible_goals", [])
    goal_signal = 50.0
    if eligible_goals:
        goal_scores = []
        for g in eligible_goals:
            try:
                goal_scores.append(float(g.get("score", 50)))
            except Exception:
                pass
        if goal_scores:
            goal_signal = sum(goal_scores) / len(goal_scores)

    priorities = priority_doc.get("integrated_priorities", [])
    priority_signal = 50.0
    if priorities:
        vals = []
        for p in priorities[:10]:
            try:
                vals.append(float(p.get("final_priority", 50)))
            except Exception:
                pass
        if vals:
            priority_signal = sum(vals) / len(vals)

    forecast_signal = 50.0
    if isinstance(forecast, dict):
        for key in ("confidence", "forecast_confidence", "score", "health_score"):
            if key in forecast:
                try:
                    val = float(forecast[key])
                    forecast_signal = val * 100 if 0 <= val <= 1 else val
                    break
                except Exception:
                    pass

    aligned = []

    for idx, opp in enumerate(opportunities[:max_opps], start=1):
        score = score_opportunity(
            opp,
            goal_signal,
            priority_signal,
            forecast_signal,
            cfg
        )

        aligned.append({
            "rank": idx,
            "id": opp.get("id"),
            "title": opp.get("title") or opp.get("name"),
            "category": opp.get("category"),
            "alignment_score": round(score, 2),
            "eligible": score >= minimum,
            "source": opp.get("source"),
            "recommendation": opp.get("recommendation"),
            "original": opp
        })

    aligned.sort(
        key=lambda x: x["alignment_score"],
        reverse=True
    )

    for i, item in enumerate(aligned, start=1):
        item["rank"] = i

    eligible = [x for x in aligned if x["eligible"]]

    report = {
        "generated_at": now(),
        "goal_signal": round(goal_signal, 2),
        "priority_signal": round(priority_signal, 2),
        "forecast_signal": round(forecast_signal, 2),
        "aligned_opportunities": aligned,
        "eligible_opportunities": eligible,
        "eligible_count": len(eligible),
        "top_opportunity": eligible[0]["title"] if eligible else None,
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_git_reset": False,
        "automatic_git_clean": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_aligned_at": now(),
        "opportunity_count": len(aligned),
        "eligible_count": len(eligible),
        "top_opportunity": report["top_opportunity"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "opportunity_count": len(aligned),
        "eligible_count": len(eligible)
    })

    return {
        "success": True,
        "status": "strategic_opportunity_alignment_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "strategic_opportunity_alignment_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "align":
        result = align()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["align", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/strategic_opportunity_alignment.py"

cat > "$CTL/strategicalignctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "strategic_opportunity_alignment.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/strategicalignctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/strategic_opportunity_alignment.py" "$CTL/strategicalignctl"

echo "[2/6] Aligning opportunities to strategy..."
python "$CTL/strategicalignctl" align

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "strategic-opportunity-alignment",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/strategicalignctl", "align"]
}

existing = next(
    (x for x in jobs if x.get("id") == job["id"]),
    None
)

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

echo "[5/6] Checking alignment status..."
python "$CTL/strategicalignctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "strategic_opportunity_alignment.py",
    root / "companyos" / "strategicalignctl",
    root / "ceo_memory" / "strategic_alignment_config.json",
    root / "ceo_memory" / "strategic_alignment_state.json",
    root / "ceo_memory" / "strategic_alignment_report.json",
    root / "ceo_memory" / "strategic_alignment_health.json",
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
        "automatic_code_changes",
        "automatic_git_reset",
        "automatic_git_clean",
        "automatic_merge",
        "automatic_deploy",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    report = json.loads(required[4].read_text())
    if "aligned_opportunities" not in report:
        errors.append("Alignment report missing aligned_opportunities")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "strategic-opportunity-alignment"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Strategic opportunity alignment scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 21 Step 2 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 2 INSTALLED"
echo " STRATEGIC OPPORTUNITY ALIGNMENT ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/strategicalignctl align"
echo "  python companyos/strategicalignctl status"
