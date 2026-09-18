from __future__ import annotations

import inspect
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from companyos.runtime.adaptive_worker_factory import Factory

ROOT = (Path.home() / "companyos").resolve()
# V31_CANONICAL_RUNTIME_ROOT
RUNTIME = Path.home() / ".companyos_runtime"
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
            "source": str(QUEUE),
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
        "verified_results_feed": str(RESULTS),
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
    # V31_LONG_RUNNING_SERVICE_ENTRYPOINT
    run()
