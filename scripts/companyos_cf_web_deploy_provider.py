#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, os, re, sys, time, urllib.request, urllib.error
from pathlib import Path

API="https://api.cloudflare.com/client/v4"
TOKEN=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
ACCOUNT=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
SUBDOMAIN=os.getenv("CLOUDFLARE_WORKERS_SUBDOMAIN","companyos-ceo").strip()
RECEIPTS=Path.home()/ "companyos"/".companyos_runtime"/"deployment_receipts"
RECEIPTS.mkdir(parents=True, exist_ok=True)

def emit(x, code=0):
    print(json.dumps(x, sort_keys=True))
    raise SystemExit(code)

def api(method, path, body=None, ctype="application/json"):
    req=urllib.request.Request(
        API+path, data=body, method=method,
        headers={"Authorization":f"Bearer {TOKEN}","Content-Type":ctype}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw=r.read().decode("utf-8","replace")
            return json.loads(raw) if raw else {"success":True}
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace")
        try: parsed=json.loads(raw)
        except Exception: parsed={"raw":raw[:4000]}
        return {"success":False,"http_status":e.code,"response":parsed}
    except Exception as e:
        return {"success":False,"error":f"{type(e).__name__}: {e}"}

def safe_name(v):
    return re.sub(r"[^a-zA-Z0-9_-]+","-",v.strip()).strip("-").lower()[:63]

def multipart(source):
    boundary=f"----companyos{int(time.time()*1000)}"
    meta=json.dumps({"main_module":"worker.js","compatibility_date":"2026-07-24"})
    chunks=[]
    def add(headers,payload):
        chunks.append(f"--{boundary}\r\n".encode())
        for h in headers: chunks.append((h+"\r\n").encode())
        chunks.append(b"\r\n"); chunks.append(payload); chunks.append(b"\r\n")
    add(['Content-Disposition: form-data; name="metadata"','Content-Type: application/json'],meta.encode())
    add(['Content-Disposition: form-data; name="worker.js"; filename="worker.js"','Content-Type: application/javascript+module'],source.encode())
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"

def receipt(obj):
    ts=int(time.time())
    path=RECEIPTS/f"cloudflare_autodeploy_{ts}.json"
    latest=RECEIPTS/"cloudflare_autodeploy_latest.json"
    text=json.dumps(obj,indent=2,sort_keys=True)+"\n"
    path.write_text(text,encoding="utf-8")
    latest.write_text(text,encoding="utf-8")
    return str(path)

if not TOKEN or not ACCOUNT:
    emit({"ok":False,"reason":"missing_cloudflare_credentials"},2)

try:
    req=json.load(sys.stdin)
except Exception as e:
    emit({"ok":False,"reason":"invalid_json_input","error":str(e)},2)

action=str(req.get("action") or "").strip().lower()

if action in {"check","status"}:
    v=api("GET","/user/tokens/verify")
    emit({"ok":bool(v.get("success")),"action":action,"workers_subdomain":SUBDOMAIN,"token_response":v})

if action!="deploy":
    emit({"ok":False,"reason":"unsupported_action","action":action},2)

name=safe_name(str(req.get("script_name") or req.get("name") or ""))
source=req.get("source") or req.get("code") or req.get("worker_source")

if not name:
    emit({"ok":False,"reason":"missing_script_name"},2)
if not isinstance(source,str) or not source.strip():
    emit({"ok":False,"reason":"missing_worker_source","note":"No deployment attempted."},2)

public=f"https://{name}.{SUBDOMAIN}.workers.dev"

if req.get("live") is not True:
    emit({"ok":True,"mode":"validated_not_uploaded","script_name":name,"public_url":public,"source_bytes":len(source.encode())})

body,ctype=multipart(source)
deploy=api("PUT",f"/accounts/{ACCOUNT}/workers/scripts/{name}",body,ctype)
if not deploy.get("success"):
    out={"ok":False,"stage":"upload","script_name":name,"provider_response":deploy}
    out["receipt"]=receipt(out)
    emit(out,1)

route=api("POST",f"/accounts/{ACCOUNT}/workers/scripts/{name}/subdomain",
          json.dumps({"enabled":True,"previews_enabled":True}).encode())
out={"ok":bool(route.get("success")),"mode":"live","script_name":name,
     "public_url":public,"deploy_response":deploy,"route_response":route}
out["receipt"]=receipt(out)
emit(out,0 if out["ok"] else 1)
