#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path.home() / "companyos"
RT = ROOT / ".companyos_runtime"
OPS = RT / "operations"
ASSETS = RT / "managed_assets.json"
REPAIRED = RT / "repaired_routes"
STATE = RT / "deployment_repair_state.json"
LEDGER = RT / "deployment_repair_ledger.jsonl"

REPAIRED.mkdir(parents=True, exist_ok=True)

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

def http(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"CompanyOS-Recovery/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return {"ok": r.status == 200, "status": r.status, "body": r.read(1200).decode("utf-8","replace")}
    except Exception as exc:
        return {"ok": False, "status": None, "error": f"{type(exc).__name__}: {exc}"}

def discover(script_name):
    cmd = f'python "{ROOT}/scripts/companyos_cf_route_discovery.py"'
    try:
        p = subprocess.run(
            cmd,
            input=json.dumps({"script_name": script_name}),
            text=True,
            shell=True,
            capture_output=True,
            timeout=90,
            cwd=str(ROOT),
            env=os.environ.copy(),
        )
        data = json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
        return {
            "ok": bool(data.get("ok")) and p.returncode == 0,
            "url": ((data.get("discovered") or {}).get("workers_dev_url")),
            "raw": data,
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "url": None}

def worker_name_from_url(url):
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        return host.split(".")[0] if host else ""
    except Exception:
        return ""

def reconcile_assets(new_urls):
    registry = load(ASSETS, {"assets":[]})
    assets = registry.get("assets") if isinstance(registry, dict) else []
    if not isinstance(assets, list):
        assets = []
    changed = 0
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        vid = asset.get("venture_id")
        if vid in new_urls:
            url = new_urls[vid]
            asset["public_url"] = url
            asset["health_url"] = url.rstrip("/") + "/health"
            asset["last_route_repair_at"] = time.time()
            changed += 1
    if changed:
        registry["assets"] = assets
        save(ASSETS, registry)
    return changed

def repair():
    results = []
    repaired_urls = {}

    for p in sorted(OPS.glob("*.json")):
        op = load(p, {})
        if not isinstance(op, dict):
            continue
        if op.get("lifecycle_state") != "operational_attention_required":
            continue

        vid = op.get("venture_id")
        health = (op.get("health") or {}).get("health_url")
        if not vid or not health:
            continue

        current_root = health[:-7] if health.endswith("/health") else health
        worker = worker_name_from_url(current_root)
        if not worker:
            results.append({"venture_id":vid,"repaired":False,"reason":"cannot_determine_worker_name"})
            continue

        d = discover(worker)
        discovered = d.get("url")

        if not discovered:
            results.append({"venture_id":vid,"repaired":False,"reason":"route_discovery_failed","details":d})
            continue

        root_check = http(discovered + "/")
        health_check = http(discovered.rstrip("/") + "/health")

        repaired = bool(root_check.get("ok") or health_check.get("ok"))

        rec = {
            "venture_id": vid,
            "worker_name": worker,
            "previous_url": current_root,
            "discovered_url": discovered,
            "root_check": root_check,
            "health_check": health_check,
            "repaired": repaired,
            "repaired_at": time.time(),
            "external_mutation_performed": False,
            "financial_action_performed": False,
        }

        save(REPAIRED / f"{vid}.json", rec)
        results.append(rec)

        if repaired:
            repaired_urls[vid] = discovered

        ledger({
            "event":"deployment_route_repair_attempted",
            "venture_id":vid,
            "worker_name":worker,
            "repaired":repaired,
            "discovered_url":discovered,
        })

    changed = reconcile_assets(repaired_urls)

    out = {
        "ok": True,
        "processed_at": time.time(),
        "repair_attempts": len(results),
        "repairs_successful": sum(1 for x in results if x.get("repaired")),
        "managed_assets_updated": changed,
        "results": results,
    }
    save(STATE, out)
    return out

action = sys.argv[1] if len(sys.argv)>1 else "status"
if action == "repair":
    emit(repair())
elif action == "status":
    emit(load(STATE, {"ok":True,"status":"not_run"}))
else:
    emit({"ok":False,"reason":"unsupported_action","action":action},2)
