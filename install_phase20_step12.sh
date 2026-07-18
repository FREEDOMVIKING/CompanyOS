#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step12_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 12 - Confidence-Weighted Priority Fusion"
echo "============================================================"

for f in \
  "$AGENTS/confidence_priority_fusion.py" \
  "$CTL/fusionctl" \
  "$MEM/confidence_priority_config.json" \
  "$MEM/confidence_priority_state.json" \
  "$MEM/confidence_priority_report.json" \
  "$MEM/confidence_priority_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/confidence_priority_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_priority_fusion": true,
  "confidence_weight": 0.35,
  "learned_score_weight": 0.35,
  "adaptive_priority_weight": 0.30,
  "minimum_fused_priority": 1,
  "maximum_fused_priority": 100,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/confidence_priority_fusion.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "confidence_priority_config.json"
ADAPTIVE = MEM / "adaptive_priority_report.json"
LEARNED = MEM / "execution_action_scores.json"

STATE = MEM / "confidence_priority_state.json"
REPORT = MEM / "confidence_priority_report.json"
HEALTH = MEM / "confidence_priority_health.json"

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

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def fuse() -> dict[str, Any]:
    cfg = load(CFG, {})
    adaptive = load(ADAPTIVE, {}).get("adaptive_priorities", [])
    learned = load(LEARNED, {}).get("actions", {})

    cw = float(cfg.get("confidence_weight", 0.35))
    lw = float(cfg.get("learned_score_weight", 0.35))
    aw = float(cfg.get("adaptive_priority_weight", 0.30))

    total = cw + lw + aw
    if total <= 0:
        cw, lw, aw, total = 0.35, 0.35, 0.30, 1.0

    fused = []

    for item in adaptive:
        action = item.get("action")
        if not action:
            continue

        adaptive_priority = float(item.get("adaptive_priority", 50))
        learned_row = learned.get(action, {})
        learned_score = float(learned_row.get("score", 50))
        confidence = float(learned_row.get("confidence", 0.50))

        confidence_percent = confidence * 100.0

        fused_priority = (
            confidence_percent * cw
            + learned_score * lw
            + adaptive_priority * aw
        ) / total

        fused_priority = clamp(
            fused_priority,
            float(cfg.get("minimum_fused_priority", 1)),
            float(cfg.get("maximum_fused_priority", 100))
        )

        fused.append({
            "action": action,
            "adaptive_priority": round(adaptive_priority, 2),
            "learned_score": round(learned_score, 2),
            "confidence": round(confidence, 4),
            "fused_priority": round(fused_priority, 2),
            "reason": item.get("reason"),
            "outcomes": item.get("outcomes", {})
        })

    fused.sort(
        key=lambda x: (
            x["fused_priority"],
            x["confidence"],
            x["learned_score"]
        ),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "fused_priorities": fused,
        "top_action": fused[0]["action"] if fused else None,
        "top_fused_priority": fused[0]["fused_priority"] if fused else None,
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_fused_at": now(),
        "action_count": len(fused),
        "top_action": report["top_action"],
        "top_fused_priority": report["top_fused_priority"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "action_count": len(fused)
    })

    return {
        "success": True,
        "status": "confidence_priority_fusion_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "confidence_priority_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "fuse":
        result = fuse()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["fuse", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/confidence_priority_fusion.py"

cat > "$CTL/fusionctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "confidence_priority_fusion.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/fusionctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/confidence_priority_fusion.py" "$CTL/fusionctl"

echo "[2/6] Running confidence-weighted fusion..."
python "$CTL/fusionctl" fuse

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "confidence-priority-fusion",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/fusionctl", "fuse"]
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

echo "[5/6] Checking fusion status..."
python "$CTL/fusionctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "confidence_priority_fusion.py",
    root / "companyos" / "fusionctl",
    root / "ceo_memory" / "confidence_priority_config.json",
    root / "ceo_memory" / "confidence_priority_state.json",
    root / "ceo_memory" / "confidence_priority_report.json",
    root / "ceo_memory" / "confidence_priority_health.json",
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
        "automatic_merge",
        "automatic_deploy",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    report = json.loads(required[4].read_text())
    if "fused_priorities" not in report:
        errors.append("Confidence priority report missing fused_priorities")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "confidence-priority-fusion"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Confidence priority fusion scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 12 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 12 INSTALLED"
echo " CONFIDENCE-WEIGHTED PRIORITY FUSION ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/fusionctl fuse"
echo "  python companyos/fusionctl status"
