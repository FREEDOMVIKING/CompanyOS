#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
ASSETS = RT / "managed_assets.json"
OPS = RT / "operations"
REPLACEMENTS = RT / "replacement_receipts"
OUT = RT / "asset_lifecycle"
RETIRED = RT / "retired_assets"
STATE = RT / "asset_lifecycle_state.json"
LEDGER = RT / "asset_lifecycle_ledger.jsonl"

OUT.mkdir(parents=True, exist_ok=True)
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
    event = dict(event)
    event.setdefault("ts", time.time())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def classify_asset(asset):
    vid = asset.get("venture_id")
    status = asset.get("status")
    public_url = asset.get("public_url")
    health_url = asset.get("health_url")
    op = load(OPS / f"{vid}.json", {}) if vid else {}
    repl = load(REPLACEMENTS / f"{vid}.json", {}) if vid else {}

    replacement_verified = bool(repl.get("verified"))
    attention = op.get("lifecycle_state") == "operational_attention_required"

    if replacement_verified:
        return "superseded_by_verified_replacement"
    if status in ("test","temporary","deprecated","retired"):
        return "legacy_or_test_asset"
    if attention and not public_url:
        return "orphaned_asset"
    if attention and health_url:
        return "broken_but_tracked"
    return "active_or_unknown"

def run():
    reg = load(ASSETS, {"assets":[]})
    assets = reg.get("assets") if isinstance(reg, dict) else []
    if not isinstance(assets, list):
        assets = []

    results = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        vid = asset.get("venture_id")
        cls = classify_asset(asset)
        action = "retain"

        if cls == "superseded_by_verified_replacement":
            action = "retire_old_route_reference"
        elif cls in ("legacy_or_test_asset","orphaned_asset"):
            action = "quarantine_from_health_loop"

        rec = {
            "venture_id": vid,
            "classification": cls,
            "recommended_action": action,
            "assessed_at": time.time(),
            "destructive_action_performed": False,
        }
        save(OUT / f"{vid or 'unknown'}.json", rec)
        results.append(rec)
        ledger({"event":"asset_lifecycle_classified","venture_id":vid,"classification":cls,"action":action})

    out = {
        "ok": True,
        "assessed_at": time.time(),
        "assets_seen": len(results),
        "results": results,
    }
    save(STATE, out)
    return out

action = sys.argv[1] if len(sys.argv)>1 else "status"
if action == "run":
    emit(run())
elif action == "status":
    emit(load(STATE, {"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
