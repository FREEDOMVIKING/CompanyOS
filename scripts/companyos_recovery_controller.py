#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
OPS = RT / "operations"
REPAIR_STATE = RT / "deployment_repair_state.json"
STATE = RT / "recovery_controller_state.json"
LEDGER = RT / "recovery_controller_ledger.jsonl"

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
    event=dict(event)
    event.setdefault("ts",time.time())
    with LEDGER.open("a",encoding="utf-8") as f:
        f.write(json.dumps(event,sort_keys=True)+"\n")

def run(cmd):
    p=subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
        timeout=600,
        cwd=str(ROOT),
    )
    try:
        out=json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
    except Exception:
        out={"ok":False,"stdout":(p.stdout or "")[:5000],"stderr":(p.stderr or "")[:5000]}
    return out,p.returncode

def recover():
    before=[]
    for p in sorted(OPS.glob("*.json")):
        d=load(p,{})
        if isinstance(d,dict) and d.get("lifecycle_state")=="operational_attention_required":
            before.append(d.get("venture_id"))

    repair,rrc=run("python scripts/companyos_deployment_repair.py repair")
    monitor,mrc=run("python scripts/companyos_postlaunch_monitor.py run")
    reconcile,orc=run("python scripts/companyos_operations_reconciler.py reconcile")

    after=[]
    for p in sorted(OPS.glob("*.json")):
        d=load(p,{})
        if isinstance(d,dict) and d.get("lifecycle_state")=="operational_attention_required":
            after.append(d.get("venture_id"))

    recovered=sorted(set(before)-set(after))
    unresolved=sorted(set(after))

    out={
        "ok": rrc==0 and mrc==0 and orc==0,
        "recovered_at":time.time(),
        "attention_before":before,
        "recovered":recovered,
        "unresolved":unresolved,
        "repair":repair,
        "monitor":monitor,
        "reconcile":reconcile,
        "automatic_rollback_performed":False,
        "external_actions_performed":False,
        "financial_actions_performed":False,
    }
    save(STATE,out)
    ledger({
        "event":"recovery_cycle_complete",
        "recovered":recovered,
        "unresolved":unresolved,
    })
    return out

action=sys.argv[1] if len(sys.argv)>1 else "status"
if action=="recover":
    emit(recover())
elif action=="status":
    emit(load(STATE,{"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
