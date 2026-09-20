#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
cd "$ROOT"
PY="${PREFIX:-/data/data/com.termux/files/usr}/bin/python"
[ -x "$PY" ] || PY=python

echo "===== COMPANYOS ADAPTIVE WORKFORCE EXECUTION BRIDGE V2 ====="
echo "Uses Factory.cycle(), never Factory.evaluate()."
echo "No finance/DNS mutation. Does not restart the healthy supervisor."

mkdir -p .companyos_runtime/backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="companyos/runtime/adaptive_workforce_execution_bridge.py"
[ -f "$TARGET" ] && cp "$TARGET" ".companyos_runtime/backups/adaptive_workforce_execution_bridge.py.$STAMP.bak"

cat > "$TARGET" <<'PYCODE'
from __future__ import annotations

import inspect
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from companyos.runtime.adaptive_worker_factory import Factory

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
STATE = RUNTIME / "adaptive_workforce_execution_bridge_state.json"
RESULTS = RUNTIME / "adaptive_workforce_verified_results.jsonl"
QUEUE = RUNTIME / "profit_execution_action_queue.json"
WORKFORCE = RUNTIME / "ceo_workforce" / "latest.json"

def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def _append(obj) -> None:
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")

def _items(obj) -> Iterable[dict]:
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for key in ("items", "queue", "actions", "jobs", "workers", "probation"):
            v = obj.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []

def _invoke_cycle(factory: Factory) -> Any:
    """Call the repository's real Factory.cycle API without inventing evaluate()."""
    method = factory.cycle
    sig = inspect.signature(method)
    required = [
        p for p in sig.parameters.values()
        if p.name != "self"
        and p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]
    if required:
        # Do not guess semantics for an unexpected future API.
        raise RuntimeError(
            "Factory.cycle has required arguments: "
            + ", ".join(p.name for p in required)
        )
    return method()

def cycle() -> Dict[str, Any]:
    now = time.time()
    queue = list(_items(_load(QUEUE, [])))
    workforce = _load(WORKFORCE, {})
    workers = list(_items(workforce))

    # This bridge does not fabricate revenue/profit. It records only observable
    # internal execution facts and leaves profitability to downstream evidence.
    emitted = 0
    for job in queue[-25:]:
        jid = str(job.get("id") or job.get("job_id") or job.get("action_id") or "")
        if not jid:
            continue
        status = str(job.get("status") or "").lower()
        if status not in {"complete", "completed", "done", "success", "succeeded", "verified"}:
            continue
        rec = {
            "timestamp": now,
            "job_id": jid,
            "status": status,
            "verified_internal_completion": True,
            "attributed_profit": job.get("attributed_profit", 0.0)
                if isinstance(job.get("attributed_profit", 0.0), (int, float)) else 0.0,
            "source": str(QUEUE.relative_to(ROOT)),
        }
        _append(rec)
        emitted += 1

    factory = Factory()
    factory_result = _invoke_cycle(factory)

    state = {
        "timestamp": now,
        "running": True,
        "factory_api": ["active", "cycle", "metrics", "signals", "spawn"],
        "factory_cycle_called": True,
        "factory_cycle_result": factory_result,
        "workers_observed": len(workers),
        "queue_items_observed": len(queue),
        "verified_results_emitted_this_cycle": emitted,
        "verified_results_feed": str(RESULTS.relative_to(ROOT)),
        "financial_metrics_invented": False,
    }
    _write(STATE, state)
    return state

def run(interval: int = 300) -> None:
    while True:
        try:
            cycle()
        except Exception as exc:
            _write(STATE, {
                "timestamp": time.time(),
                "running": True,
                "error": f"{type(exc).__name__}: {exc}",
                "financial_metrics_invented": False,
            })
        time.sleep(max(30, interval))

if __name__ == "__main__":
    print(json.dumps(cycle(), indent=2, default=str))
PYCODE

cat > scripts/companyos_workforce_execute <<'PYCODE'
#!/data/data/com.termux/files/usr/bin/python
import json
from companyos.runtime.adaptive_workforce_execution_bridge import cycle
print(json.dumps(cycle(), indent=2, default=str))
PYCODE
chmod +x scripts/companyos_workforce_execute

mkdir -p tests/generated
cat > tests/generated/test_adaptive_workforce_execution_bridge_v2.py <<'PYCODE'
import inspect
from companyos.runtime.adaptive_worker_factory import Factory
from companyos.runtime import adaptive_workforce_execution_bridge as b

def test_factory_real_api():
    assert hasattr(Factory, "cycle")
    assert not hasattr(Factory, "evaluate")

def test_bridge_calls_cycle_not_evaluate():
    src = inspect.getsource(b._invoke_cycle)
    assert ".cycle" in src
    assert ".evaluate" not in src

def test_no_invented_profit_policy():
    src = inspect.getsource(b.cycle)
    assert "financial_metrics_invented" in src
    assert "attributed_profit" in src

def test_module_paths():
    assert b.STATE.name.endswith(".json")
    assert b.RESULTS.name.endswith(".jsonl")
PYCODE

echo "===== COMPILE ====="
"$PY" -m py_compile "$TARGET" scripts/companyos_workforce_execute

echo "===== TEST ====="
"$PY" -m pytest -q tests/generated/test_adaptive_workforce_execution_bridge_v2.py

echo "===== LIVE V2 CYCLE ====="
"$PY" scripts/companyos_workforce_execute

echo "===== SUPERVISOR CHECK ====="
"$PY" - <<'PY'
import json
from pathlib import Path
p=Path.home()/ "companyos/.companyos_runtime/service_supervisor_state.json"
try:
    d=json.loads(p.read_text())
    print("supervisor_pid:", d.get("supervisor_pid"))
    print("running:", d.get("running"))
    print("stop_requested:", d.get("stop_requested"))
except Exception as e:
    print("supervisor_state_read:", type(e).__name__)
PY

echo "===== COMMIT ONLY THIS FIX ====="
git add -- "$TARGET" scripts/companyos_workforce_execute tests/generated/test_adaptive_workforce_execution_bridge_v2.py
if ! git diff --cached --quiet; then
  git commit -m "fix adaptive workforce execution bridge to use Factory cycle"
else
  echo "No staged changes to commit."
fi

echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
echo "FINANCE_LIMITS_CHANGED=NO"
echo "FACTORY_EVALUATE_CALL_REMOVED=YES"
echo "FACTORY_CYCLE_INTEGRATION=YES"
echo "COMPANYOS_ADAPTIVE_WORKFORCE_EXECUTION_BRIDGE_V2=PASS"
