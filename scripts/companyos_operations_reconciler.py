#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
POST = RT / "postlaunch"
HANDOFFS = RT / "deployment_handoffs"
OPS = RT / "operations"
STATE = RT / "operations_reconciler_state.json"
LEDGER = RT / "operations_reconciler_ledger.jsonl"

OPS.mkdir(parents=True, exist_ok=True)

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def ledger(event):
    event = dict(event)
    event.setdefault("ts", time.time())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def reconcile():
    ventures = {}

    for p in HANDOFFS.glob("*.json"):
        h = load(p, {})
        vid = h.get("venture_id")
        if vid:
            ventures.setdefault(vid, {})["handoff"] = h

    for p in POST.glob("*.json"):
        m = load(p, {})
        vid = m.get("venture_id")
        if vid:
            ventures.setdefault(vid, {})["monitor"] = m

    results = []

    for vid, data in sorted(ventures.items()):
        handoff = data.get("handoff") or {}
        monitor = data.get("monitor") or {}

        if monitor:
            lifecycle = "operational_healthy" if monitor.get("healthy") else "operational_attention_required"
        else:
            lifecycle = handoff.get("operations_state") or "unknown"

        rollback_recommended = bool(monitor and not monitor.get("healthy"))

        record = {
            "venture_id": vid,
            "updated_at": time.time(),
            "lifecycle_state": lifecycle,
            "rollback_recommended": rollback_recommended,
            "automatic_rollback_performed": False,
            "release_archive": handoff.get("release_archive"),
            "release_sha256": handoff.get("release_sha256"),
            "health": monitor,
            "external_actions_require_existing_gate": True,
        }

        save(OPS / f"{vid}.json", record)
        results.append(record)
        ledger({
            "event":"operations_reconciled",
            "venture_id":vid,
            "lifecycle_state":lifecycle,
            "rollback_recommended":rollback_recommended,
        })

    out = {
        "ok": True,
        "reconciled_at": time.time(),
        "ventures_reconciled": len(results),
        "attention_required": sum(1 for x in results if x["rollback_recommended"]),
        "results": results,
    }
    save(STATE, out)
    return out

action = __import__("sys").argv[1] if len(__import__("sys").argv)>1 else "status"
if action == "reconcile":
    emit(reconcile())
elif action == "status":
    emit(load(STATE, {"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
