#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
ASSETS = RT / "managed_assets.json"
LIFE = RT / "asset_lifecycle"
RETIRED = RT / "retired_assets"
STATE = RT / "infrastructure_cleanup_state.json"
LEDGER = RT / "infrastructure_cleanup_ledger.jsonl"

RETIRED.mkdir(parents=True, exist_ok=True)

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

def run():
    reg = load(ASSETS, {"assets":[]})
    assets = reg.get("assets") if isinstance(reg,dict) else []
    if not isinstance(assets,list):
        assets=[]

    active=[]
    retired=[]
    quarantined=[]

    for asset in assets:
        if not isinstance(asset,dict):
            continue
        vid=asset.get("venture_id")
        life=load(LIFE/f"{vid}.json",{})
        action=life.get("recommended_action")

        if action=="retire_old_route_reference":
            snapshot=dict(asset)
            snapshot["retired_at"]=time.time()
            snapshot["retirement_reason"]="verified_replacement_exists"
            save(RETIRED/f"{vid}.json",snapshot)
            asset["monitoring_enabled"]=False
            asset["status"]="superseded"
            retired.append(vid)
            active.append(asset)

        elif action=="quarantine_from_health_loop":
            asset["monitoring_enabled"]=False
            asset["status"]="quarantined"
            asset["quarantined_at"]=time.time()
            quarantined.append(vid)
            active.append(asset)

        else:
            if "monitoring_enabled" not in asset:
                asset["monitoring_enabled"]=True
            active.append(asset)

    reg["assets"]=active
    save(ASSETS,reg)

    out={
        "ok":True,
        "processed_at":time.time(),
        "retired_count":len(retired),
        "quarantined_count":len(quarantined),
        "retired":retired,
        "quarantined":quarantined,
        "destructive_provider_delete_performed":False,
    }
    save(STATE,out)
    ledger({"event":"infrastructure_cleanup_complete","retired":retired,"quarantined":quarantined})
    return out

action=sys.argv[1] if len(sys.argv)>1 else "status"
if action=="run":
    emit(run())
elif action=="status":
    emit(load(STATE,{"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
