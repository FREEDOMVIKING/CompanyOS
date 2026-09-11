#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
RELEASES = RT / "releases"
HANDOFFS = RT / "deployment_handoffs"
OPS = RT / "operations"
STATE = RT / "launch_operations_state.json"
LEDGER = RT / "launch_operations_ledger.jsonl"

for p in (HANDOFFS, OPS):
    p.mkdir(parents=True, exist_ok=True)

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

def make_handoff(receipt):
    vid = receipt.get("venture_id")
    if not vid:
        return None
    handoff = {
        "venture_id": vid,
        "created_at": time.time(),
        "release_archive": receipt.get("archive"),
        "release_sha256": receipt.get("sha256"),
        "release_status": receipt.get("release_status"),
        "ready_for_deployment_handoff": bool(receipt.get("ready_for_deployment_handoff")),
        "external_deployment_authorized": False,
        "deployment_mode": "prepared_not_executed",
        "operations_state": "awaiting_existing_launch_gate",
    }
    save(HANDOFFS / f"{vid}.json", handoff)
    ledger({"event":"deployment_handoff_created","venture_id":vid})
    return handoff

def process():
    results = []
    for p in sorted(RELEASES.glob("*-latest.json")):
        rec = load(p, {})
        if not isinstance(rec, dict) or not rec.get("ready_for_deployment_handoff"):
            continue
        h = make_handoff(rec)
        if not h:
            continue
        results.append(h)

    state = {
        "ok": True,
        "processed_at": time.time(),
        "handoffs_created": len(results),
        "results": results,
    }
    save(STATE, state)
    return state

action = sys.argv[1] if len(sys.argv) > 1 else "status"
if action == "process":
    emit(process())
elif action == "status":
    emit(load(STATE, {"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
