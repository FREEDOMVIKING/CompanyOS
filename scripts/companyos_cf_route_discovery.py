#!/data/data/com.termux/files/usr/bin/python
import json, os, sys, urllib.request, urllib.error

API="https://api.cloudflare.com/client/v4"
TOKEN=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
ACCOUNT=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()

def get(path):
    req=urllib.request.Request(
        API+path,
        headers={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read().decode("utf-8","replace")
            return json.loads(raw) if raw else {"success":True}
    except urllib.error.HTTPError as e:
        raw=e.read().decode("utf-8","replace")
        try: parsed=json.loads(raw)
        except Exception: parsed={"raw":raw[:4000]}
        return {"success":False,"http_status":e.code,"response":parsed}
    except Exception as e:
        return {"success":False,"error":f"{type(e).__name__}: {e}"}

try:
    req=json.load(sys.stdin)
except Exception as e:
    print(json.dumps({"ok":False,"reason":"invalid_json_input","error":str(e)}))
    raise SystemExit(2)

script=str(req.get("script_name") or "").strip()
if not script:
    print(json.dumps({"ok":False,"reason":"missing_script_name"}))
    raise SystemExit(2)

a=get(f"/accounts/{ACCOUNT}/workers/subdomain")
s=get(f"/accounts/{ACCOUNT}/workers/scripts/{script}/subdomain")

out={"ok":bool(a.get("success")) and bool(s.get("success")),
     "script_name":script,
     "account_subdomain_response":a,
     "script_subdomain_response":s,
     "discovered":{}}

if out["ok"]:
    sub=(a.get("result") or {}).get("subdomain")
    enabled=(s.get("result") or {}).get("enabled")
    out["discovered"]["workers_dev_enabled"]=bool(enabled)
    if sub and enabled:
        out["discovered"]["workers_dev_url"]=f"https://{script}.{sub}.workers.dev"

print(json.dumps(out,sort_keys=True))
raise SystemExit(0 if out["ok"] else 1)
