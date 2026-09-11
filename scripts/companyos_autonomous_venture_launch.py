#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path.home() / "companyos"
RUNTIME = ROOT / ".companyos_runtime"
RECEIPTS = RUNTIME / "deployment_receipts"
LEDGER = RUNTIME / "venture_launch_ledger.jsonl"
REGISTRY = RUNTIME / "managed_assets.json"
ASSET_DIR = RUNTIME / "managed_assets"

for p in (RECEIPTS, ASSET_DIR):
    p.mkdir(parents=True, exist_ok=True)

def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def slug(v):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", v.strip()).strip("-").lower()[:48]

def ledger(event):
    event.setdefault("ts", time.time())
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

def save_receipt(obj, vid):
    p = RECEIPTS / f"venture_launch_{vid}_{int(time.time())}.json"
    latest = RECEIPTS / "venture_launch_latest.json"
    text = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    p.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    return str(p)

def load_registry():
    try:
        d = json.loads(REGISTRY.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {"assets":[]}
    except Exception:
        return {"assets":[]}

def save_registry(d):
    tmp = REGISTRY.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(REGISTRY)

def http_status(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"CompanyOS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(2000).decode("utf-8","replace")
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def discover_cloudflare_url(script_name):
    cmd = f'python "{ROOT}/scripts/companyos_cf_route_discovery.py"'
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps({"script_name": script_name}),
            text=True,
            shell=True,
            capture_output=True,
            timeout=90,
            cwd=str(ROOT),
            env=os.environ.copy()
        )
        data = json.loads((proc.stdout or "").strip()) if (proc.stdout or "").strip() else {}
        return {
            "ok": bool(data.get("ok")) and proc.returncode == 0,
            "returncode": proc.returncode,
            "response": data,
            "url": ((data.get("discovered") or {}).get("workers_dev_url")),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "url": None}

def stabilized_http_check(url, attempts=8, base_delay=4):
    history = []
    for attempt in range(1, attempts + 1):
        status, body = http_status(url, timeout=25)
        history.append({"attempt": attempt, "status": status, "detail": body[:500]})
        if status == 200:
            return {"ok": True, "status": status, "body": body, "attempts_used": attempt, "history": history}
        if attempt < attempts:
            time.sleep(min(base_delay * attempt, 20))
    return {
        "ok": False,
        "status": history[-1]["status"] if history else None,
        "body": history[-1]["detail"] if history else "",
        "attempts_used": attempts,
        "history": history,
    }

try:
    req = json.load(sys.stdin)
except Exception as e:
    emit({"ok":False,"reason":"invalid_json_input","error":str(e)},2)

v = req.get("venture")
if not isinstance(v, dict):
    emit({"ok":False,"reason":"missing_venture"},2)

name = str(v.get("name") or "").strip()
vid = slug(str(v.get("venture_id") or name))
approved = v.get("approved") is True
launch_ready = v.get("launch_ready") is True
live = req.get("live") is True

if not name or not vid:
    emit({"ok":False,"reason":"missing_venture_identity"},2)
if not approved:
    emit({"ok":False,"reason":"venture_not_approved","venture_id":vid,"note":"No deployment attempted."},3)
if not launch_ready:
    emit({"ok":False,"reason":"venture_not_launch_ready","venture_id":vid,"note":"No deployment attempted."},3)

tagline = str(v.get("tagline") or "Built and launched by CompanyOS")
description = str(v.get("description") or "")
worker = slug(str(v.get("worker_name") or f"venture-{vid}"))

html = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    f"<title>{name}</title></head><body>"
    f"<main><h1>{name}</h1><h2>{tagline}</h2><p>{description}</p>"
    "<p>Managed by CompanyOS</p></main></body></html>"
)

source = (
    "export default { async fetch(request) {"
    "const url = new URL(request.url);"
    "if (url.pathname === '/health') {"
    "return Response.json("
    + json.dumps({"ok":True,"venture_id":vid,"venture_name":name,"status":"healthy","managed_by":"CompanyOS"})
    + ");}"
    "return new Response("
    + json.dumps(html)
    + ", {headers:{'content-type':'text/html; charset=UTF-8'}});"
    "} };"
)

ledger({"event":"venture_launch_started","venture_id":vid,"worker_name":worker,"live":live})

cmd = os.getenv("COMPANYOS_EXECUTIVE_WEB_DEPLOY_CMD","").strip()
if not cmd:
    emit({"ok":False,"reason":"missing_executive_deploy_command"},2)

payload = {"name":worker,"live":live,"source":source}

try:
    p = subprocess.run(cmd, input=json.dumps(payload), text=True, shell=True,
                       capture_output=True, timeout=240, cwd=str(ROOT), env=os.environ.copy())
except Exception as e:
    out={"ok":False,"venture_id":vid,"stage":"executive_deploy_call","error":f"{type(e).__name__}: {e}"}
    out["receipt"]=save_receipt(out,vid)
    ledger({"event":"venture_launch_failed","venture_id":vid,"stage":"executive_deploy_call"})
    emit(out,1)

try:
    deploy = json.loads((p.stdout or "").strip())
except Exception:
    deploy={"ok":False,"reason":"non_json_executive_response","stdout":(p.stdout or "")[:4000],"stderr":(p.stderr or "")[:4000]}

provider = deploy.get("provider") or {}
constructed_url = provider.get("public_url")
route_discovery = discover_cloudflare_url(worker) if live else {"ok": True, "url": constructed_url}
public_url = route_discovery.get("url") or constructed_url

out = {
    "ok": bool(deploy.get("ok")) and p.returncode == 0,
    "deployment_status": "DEPLOYED" if (bool(deploy.get("ok")) and p.returncode == 0) else "DEPLOY_FAILED",
    "venture_id": vid,
    "venture_name": name,
    "worker_name": worker,
    "live": live,
    "public_url": public_url,
    "constructed_url": constructed_url,
    "route_discovery": route_discovery,
    "executive_deploy": deploy
}

if out["ok"] and live and public_url:
    root_check = stabilized_http_check(public_url + "/")
    health_check = stabilized_http_check(public_url + "/health")
    out["verification"] = {
        "root_http": root_check.get("status"),
        "health_http": health_check.get("status"),
        "root_ok": bool(root_check.get("ok")),
        "health_ok": bool(health_check.get("ok")),
        "root_attempts_used": root_check.get("attempts_used"),
        "health_attempts_used": health_check.get("attempts_used"),
        "root_history": root_check.get("history"),
        "health_history": health_check.get("history"),
        "health_body": str(health_check.get("body") or "")[:1500],
        "stabilization_enabled": True
    }
    if root_check.get("ok") and health_check.get("ok"):
        out["verification_status"] = "PUBLICLY_VERIFIED"
    else:
        out["verification_status"] = "DEPLOYED_NOT_YET_PUBLICLY_VERIFIED"
        out["stage"] = "post_deploy_verification_after_retries"

if out.get("deployment_status") == "DEPLOYED":
    registry = load_registry()
    assets = registry.setdefault("assets", [])
    prior = next((dict(x) for x in assets if x.get("venture_id")==vid), None)
    record = {
        "venture_id":vid,
        "name":name,
        "worker_name":worker,
        "public_url":public_url,
        "health_url":(public_url + "/health") if public_url else None,
        "status": (
            "live_verified"
            if out.get("verification_status") == "PUBLICLY_VERIFIED"
            else ("deployed_pending_public_verification" if live else "validated")
        ),
        "managed_by":"CompanyOS",
        "updated_at":time.time(),
        "previous":prior
    }
    registry["assets"] = [x for x in assets if x.get("venture_id") != vid] + [record]
    save_registry(registry)
    ap = ASSET_DIR / f"{vid}.json"
    ap.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out["managed_asset"] = record
    out["managed_asset_path"] = str(ap)

out["receipt"] = save_receipt(out,vid)
ledger({
    "event":"venture_launch_completed" if out["ok"] else "venture_launch_failed",
    "venture_id":vid,
    "worker_name":worker,
    "public_url":public_url,
    "live":live,
    "receipt":out["receipt"],
    "stage":out.get("stage")
})
if out.get("deployment_status") == "DEPLOYED" and live and out.get("verification_status") != "PUBLICLY_VERIFIED":
    out["ok"] = True
emit(out, 0 if out["ok"] else 1)
