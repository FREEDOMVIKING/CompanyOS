#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
LOGS="$ROOT/logs"
BACKUP="$ROOT/backups/phase22_bundle1_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$LOGS" "$BACKUP"

echo "============================================================"
echo " PHASE 22 BUNDLE 1 - AUTONOMOUS AI OPERATIONS CORE"
echo "============================================================"

# ------------------------------------------------------------
# Backup anything this installer may replace.
# ------------------------------------------------------------
for f in \
  "$AGENTS/autonomy_controller.py" \
  "$AGENTS/ai_retry_policy.py" \
  "$AGENTS/model_fallback_router.py" \
  "$AGENTS/cycle_deduplicator.py" \
  "$AGENTS/api_usage_tracker.py" \
  "$AGENTS/ceo_live_reasoning_bridge.py" \
  "$CTL/autonomyctl" \
  "$CTL/usagetrackerctl" \
  "$MEM/autonomy_core_config.json" \
  "$MEM/autonomy_core_state.json" \
  "$MEM/autonomy_core_report.json" \
  "$MEM/autonomy_core_health.json" \
  "$MEM/api_usage_state.json" \
  "$MEM/model_fallback_config.json" \
  "$MEM/autonomy_cycle_history.json" \
  "$MEM/ceo_live_reasoning_input.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

# ------------------------------------------------------------
# 1. Core configuration
# ------------------------------------------------------------
cat > "$MEM/autonomy_core_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_cycle": true,
  "max_specialist_tasks_per_cycle": 5,
  "max_cycle_failures_before_stop": 3,
  "cycle_dedup_ttl_seconds": 86400,
  "api_daily_request_limit": 150,
  "api_daily_token_budget": 250000,
  "retry": {
    "max_attempts": 3,
    "base_delay_seconds": 2,
    "max_delay_seconds": 30,
    "retry_http_codes": [408, 429, 500, 502, 503, 504]
  },
  "fallback_models": [
    "openrouter/free"
  ],
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_fund_transfer": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$MEM/model_fallback_config.json" <<'JSON'
{
  "enabled": true,
  "provider": "openrouter",
  "models": [
    "openrouter/free"
  ],
  "fallback_on_empty_response": true,
  "fallback_on_http_errors": [408, 429, 500, 502, 503, 504],
  "automatic_external_write": false,
  "automatic_spending": false
}
JSON

# ------------------------------------------------------------
# 2. Retry policy helper
# ------------------------------------------------------------
cat > "$AGENTS/ai_retry_policy.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")

def run_with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 2.0,
    max_delay_seconds: float = 30.0,
) -> T:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            delay = min(max_delay_seconds, base_delay_seconds * (2 ** (attempt - 1)))
            time.sleep(delay)

    assert last_error is not None
    raise last_error
PY

chmod +x "$AGENTS/ai_retry_policy.py"

# ------------------------------------------------------------
# 3. Model fallback router
# ------------------------------------------------------------
cat > "$AGENTS/model_fallback_router.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
CFG = MEM / "model_fallback_config.json"

def load() -> dict[str, Any]:
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {"enabled": True, "models": ["openrouter/free"]}

def models() -> list[str]:
    cfg = load()
    values = cfg.get("models", ["openrouter/free"])
    return [str(x) for x in values if x] or ["openrouter/free"]

def primary_model() -> str:
    return models()[0]

if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "model_fallback_router_status",
        "models": models(),
        "primary_model": primary_model()
    }, indent=2))
PY

chmod +x "$AGENTS/model_fallback_router.py"

# ------------------------------------------------------------
# 4. Cycle deduplicator
# ------------------------------------------------------------
cat > "$AGENTS/cycle_deduplicator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
HISTORY = MEM / "autonomy_cycle_history.json"

def load() -> dict[str, Any]:
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except Exception:
        return {"entries": {}}

def save(data: dict[str, Any]) -> None:
    HISTORY.write_text(json.dumps(data, indent=2), encoding="utf-8")

def fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def recently_seen(payload: Any, ttl_seconds: int) -> bool:
    data = load()
    entries = data.setdefault("entries", {})
    fp = fingerprint(payload)
    now = time.time()

    stale = [k for k, ts in entries.items() if now - float(ts) > ttl_seconds]
    for key in stale:
        entries.pop(key, None)

    seen = fp in entries
    entries[fp] = now
    save(data)
    return seen

if __name__ == "__main__":
    print(json.dumps({"success": True, "status": "cycle_deduplicator_ready"}, indent=2))
PY

chmod +x "$AGENTS/cycle_deduplicator.py"

# ------------------------------------------------------------
# 5. API usage tracker
# ------------------------------------------------------------
cat > "$AGENTS/api_usage_tracker.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
STATE = MEM / "api_usage_state.json"

def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load() -> dict[str, Any]:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    if data.get("date") != today():
        data = {
            "date": today(),
            "requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "updated_at": now()
        }
    return data

def save(data: dict[str, Any]) -> None:
    data["updated_at"] = now()
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def record(requests: int = 1, input_tokens: int = 0, output_tokens: int = 0) -> dict[str, Any]:
    data = load()
    data["requests"] += int(requests)
    data["input_tokens"] += int(input_tokens)
    data["output_tokens"] += int(output_tokens)
    data["total_tokens"] = data["input_tokens"] + data["output_tokens"]
    save(data)
    return data

def status() -> dict[str, Any]:
    return load()

action = sys.argv[1] if len(sys.argv) > 1 else "status"

if action == "record":
    requests = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    input_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    output_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    result = record(requests, input_tokens, output_tokens)
else:
    result = status()

print(json.dumps({
    "success": True,
    "status": "api_usage_tracker",
    "usage": result
}, indent=2))
PY

chmod +x "$AGENTS/api_usage_tracker.py"

cat > "$CTL/usagetrackerctl" <<'PY'
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

root = Path.home() / "companyos"
raise SystemExit(
    subprocess.call(
        [sys.executable, str(root / "agents" / "api_usage_tracker.py"), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/usagetrackerctl"

# ------------------------------------------------------------
# 6. Live CEO reasoning bridge
# ------------------------------------------------------------
cat > "$AGENTS/ceo_live_reasoning_bridge.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

INSIGHTS = MEM / "validated_insights.json"
DECISIONS = MEM / "ceo_decision_candidates.json"
OUT = MEM / "ceo_live_reasoning_input.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def build() -> dict[str, Any]:
    insights = load(INSIGHTS, {}).get("insights", [])
    decisions = load(DECISIONS, {}).get("decisions", [])

    payload = {
        "generated_at": now(),
        "validated_insights": insights[-50:],
        "decision_candidates": decisions[-50:],
        "reasoning_boundary": "internal_non_destructive_only",
        "external_authority_granted": False
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "ceo_live_reasoning_bridge_complete",
        "payload": build()
    }, indent=2))
PY

chmod +x "$AGENTS/ceo_live_reasoning_bridge.py"

# ------------------------------------------------------------
# 7. Master autonomy controller
# ------------------------------------------------------------
cat > "$AGENTS/autonomy_controller.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "autonomy_core_config.json"
STATE = MEM / "autonomy_core_state.json"
REPORT = MEM / "autonomy_core_report.json"
HEALTH = MEM / "autonomy_core_health.json"

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

def call(args: list[str], timeout: int = 900) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=os.environ.copy()
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-5000:],
            "stderr": proc.stderr[-2500:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

PIPELINE = [
    ("readiness_recovery", ["python", "companyos/recovery2ctl", "run"]),
    ("opportunity_cycle", ["python", "companyos/opportunitycyclectl", "run"]),
    ("portfolio_allocation", ["python", "companyos/opportunityportfolioctl", "allocate"]),
    ("portfolio_rebalance", ["python", "companyos/portfoliorebalancectl", "rebalance"]),
    ("portfolio_performance", ["python", "companyos/portfolioperformancectl", "evaluate"]),
    ("internal_resources", ["python", "companyos/resourceallocatectl", "allocate"]),
    ("specialist_delegation", ["python", "companyos/specialistdelegatectl", "plan"]),
    ("multiagent_routing", ["python", "companyos/multiagentroutectl", "route"]),
    ("specialist_result_requests", ["python", "companyos/specialistresultctl", "collect"]),
    ("governed_queue", ["python", "companyos/governedqueuectl", "enqueue"]),
    ("governed_worker", ["python", "companyos/governedworkerctl", "run"]),
    ("specialist_bridge", ["python", "companyos/specialistbridgectl", "bridge"]),
    ("live_specialists", ["python", "companyos/livespecialistctl", "run"]),
    ("result_bridge", ["python", "companyos/liveresultbridgectl", "integrate"]),
    ("validated_insights", ["python", "companyos/insightrefreshctl", "refresh"]),
    ("ceo_insight_integration", ["python", "companyos/specialistinsightctl", "integrate"]),
    ("ceo_decision_synthesis", ["python", "companyos/ceoinsightdecisionctl", "synthesize"]),
    ("ceo_governance", ["python", "companyos/ceodecisiongovernctl", "govern"]),
    ("governed_planning", ["python", "companyos/governedplanctl", "plan"]),
    ("ceo_reasoning_bridge", ["python", "agents/ceo_live_reasoning_bridge.py"])
]

def run_cycle() -> dict[str, Any]:
    cfg = load(CFG, {})
    failures_before_stop = int(cfg.get("max_cycle_failures_before_stop", 3))

    steps = []
    failures = []

    for name, cmd in PIPELINE:
        result = call(cmd)
        steps.append({"step": name, "result": result})

        if not result.get("success", False):
            failures.append(name)

        if len(failures) >= failures_before_stop:
            break

    report = {
        "generated_at": now(),
        "steps": steps,
        "failure_count": len(failures),
        "failed_steps": failures,
        "api_key_available": bool(
            os.getenv("OPENROUTER_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        ),
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_fund_transfer": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_cycle_at": now(),
        "failure_count": len(failures),
        "failed_steps": failures
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "autonomous_ai_operations_cycle_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "autonomy_core_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "config": load(CFG, {})
    }

action = sys.argv[1] if len(sys.argv) > 1 else "status"

if action == "run":
    result = run_cycle()
elif action == "status":
    result = status()
else:
    result = {
        "success": False,
        "status": "unknown_action",
        "allowed": ["run", "status"]
    }

print(json.dumps(result, indent=2))
raise SystemExit(0 if result.get("success") else 1)
PY

chmod +x "$AGENTS/autonomy_controller.py"

cat > "$CTL/autonomyctl" <<'PY'
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "autonomy_controller.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/autonomyctl"

# ------------------------------------------------------------
# 8. Compile
# ------------------------------------------------------------
echo "[1/8] Compiling Phase 22 core..."
python -m py_compile \
  "$AGENTS/ai_retry_policy.py" \
  "$AGENTS/model_fallback_router.py" \
  "$AGENTS/cycle_deduplicator.py" \
  "$AGENTS/api_usage_tracker.py" \
  "$AGENTS/ceo_live_reasoning_bridge.py" \
  "$AGENTS/autonomy_controller.py" \
  "$CTL/usagetrackerctl" \
  "$CTL/autonomyctl"

# ------------------------------------------------------------
# 9. Initialize state
# ------------------------------------------------------------
echo "[2/8] Initializing usage tracker..."
python "$CTL/usagetrackerctl" status

echo "[3/8] Building CEO live reasoning input..."
python "$AGENTS/ceo_live_reasoning_bridge.py"

# ------------------------------------------------------------
# 10. Register master scheduled cycle
# ------------------------------------------------------------
echo "[4/8] Registering master autonomy scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "autonomous-ai-operations-core",
    "enabled": True,
    "interval_seconds": 3600,
    "command": ["python", "companyos/autonomyctl", "run"]
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

# ------------------------------------------------------------
# 11. Restart operations scheduler
# ------------------------------------------------------------
echo "[5/8] Restarting operations scheduler..."
python "$CTL/operationsctl" restart

# ------------------------------------------------------------
# 12. Run a controlled master cycle
# ------------------------------------------------------------
echo "[6/8] Running one controlled autonomy cycle..."
python "$CTL/autonomyctl" run || true

# ------------------------------------------------------------
# 13. Status
# ------------------------------------------------------------
echo "[7/8] Checking master autonomy status..."
python "$CTL/autonomyctl" status

# ------------------------------------------------------------
# 14. Full verification
# ------------------------------------------------------------
echo "[8/8] Verifying Phase 22 Bundle 1..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []
warnings = []

required = [
    root/"agents"/"ai_retry_policy.py",
    root/"agents"/"model_fallback_router.py",
    root/"agents"/"cycle_deduplicator.py",
    root/"agents"/"api_usage_tracker.py",
    root/"agents"/"ceo_live_reasoning_bridge.py",
    root/"agents"/"autonomy_controller.py",
    root/"companyos"/"usagetrackerctl",
    root/"companyos"/"autonomyctl",
    root/"ceo_memory"/"autonomy_core_config.json",
    root/"ceo_memory"/"model_fallback_config.json",
    root/"ceo_memory"/"api_usage_state.json",
    root/"ceo_memory"/"ceo_live_reasoning_input.json",
    root/"ceo_memory"/"autonomous_operations_config.json"
]

for path in required:
    if not path.exists() or path.stat().st_size <= 0:
        errors.append(f"Missing/empty: {path}")

for path in required[:8]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

cfg = json.loads((root/"ceo_memory"/"autonomy_core_config.json").read_text())

for key in [
    "automatic_external_write",
    "automatic_customer_contact",
    "automatic_publication",
    "automatic_spending",
    "automatic_fund_transfer",
    "automatic_code_changes",
    "automatic_merge",
    "automatic_deploy",
    "automatic_destructive_actions"
]:
    if cfg.get(key) is not False:
        errors.append(f"{key} must remain disabled")

sched = json.loads((root/"ceo_memory"/"autonomous_operations_config.json").read_text())
job = next(
    (x for x in sched.get("jobs", [])
     if x.get("id") == "autonomous-ai-operations-core"),
    None
)

if not job or job.get("enabled") is not True:
    errors.append("Master autonomy scheduler job missing/disabled")

runtime_cfg_path = root/"ceo_memory"/"specialist_runtime_config.json"
if runtime_cfg_path.exists():
    runtime_cfg = json.loads(runtime_cfg_path.read_text())
    if runtime_cfg.get("api_key_env") == "OPENROUTER_API_KEY":
        import os
        if not os.getenv("OPENROUTER_API_KEY", "").strip():
            warnings.append("OPENROUTER_API_KEY is not loaded in this shell.")
else:
    warnings.append("specialist_runtime_config.json not found; live specialist runtime may not be configured.")

print("--------------------------------------------")
print("PHASE 22 BUNDLE 1 VERIFICATION")
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")

for error in errors:
    print("ERROR:", error)

for warning in warnings:
    print("WARNING:", warning)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 22 BUNDLE 1 INSTALLED"
echo " AUTONOMOUS AI OPERATIONS CORE ACTIVE"
echo " Errors: 0"
echo "============================================================"
echo
echo "Master commands:"
echo "  python companyos/autonomyctl run"
echo "  python companyos/autonomyctl status"
echo "  python companyos/usagetrackerctl status"
echo
echo "Bundle includes:"
echo "  - Master autonomy controller"
echo "  - Live CEO reasoning bridge"
echo "  - Retry policy helper"
echo "  - Model fallback router"
echo "  - Cycle deduplication helper"
echo "  - API usage tracking"
echo "  - Scheduler integration"
echo "  - End-to-end verification"
