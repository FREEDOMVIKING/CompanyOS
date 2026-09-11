#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
ASSETS = RT / "managed_assets.json"
OUT = RT / "postlaunch"
STATE = RT / "postlaunch_monitor_state.json"
LEDGER = RT / "postlaunch_monitor_ledger.jsonl"

OUT.mkdir(parents=True, exist_ok=True)

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

def check(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"CompanyOS-PostLaunch/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(1500).decode("utf-8","replace")
            return {"ok": True, "status": r.status, "body": body}
    except Exception as exc:
        return {"ok": False, "status": None, "error": f"{type(exc).__name__}: {exc}"}

def run():
    registry = load(ASSETS, {"assets":[]})
    assets = registry.get("assets") if isinstance(registry, dict) else []
    if not isinstance(assets, list):
        assets = []

    results = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if asset.get('monitoring_enabled') is False:
            continue
        vid = asset.get("venture_id")
        health = asset.get("health_url")
        if not vid or not health:
            continue

        result = check(health)
        record = {
            "venture_id": vid,
            "checked_at": time.time(),
            "health_url": health,
            "healthy": bool(result.get("ok") and result.get("status") == 200),
            "http_status": result.get("status"),
            "error": result.get("error"),
        }
        save(OUT / f"{vid}.json", record)
        results.append(record)
        ledger({
            "event":"postlaunch_health_check",
            "venture_id":vid,
            "healthy":record["healthy"],
            "http_status":record["http_status"],
        })

    state = {
        "ok": True,
        "checked_at": time.time(),
        "assets_checked": len(results),
        "healthy": sum(1 for x in results if x["healthy"]),
        "unhealthy": sum(1 for x in results if not x["healthy"]),
        "results": results,
    }
    save(STATE, state)
    return state

action = __import__("sys").argv[1] if len(__import__("sys").argv)>1 else "status"
if action == "run":
    emit(run())
elif action == "status":
    emit(load(STATE, {"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
