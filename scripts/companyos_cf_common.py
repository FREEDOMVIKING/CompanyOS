from __future__ import annotations
import json, os, sys, urllib.error, urllib.parse, urllib.request
API = "https://api.cloudflare.com/client/v4"

def emit(obj: dict, code: int = 0) -> None:
    print(json.dumps(obj, sort_keys=True))
    raise SystemExit(code)

def read_req() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception as exc:
        emit({"ok": False, "reason": "invalid_json", "error": f"{type(exc).__name__}: {exc}"}, 2)

def token() -> str:
    t = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not t:
        emit({"ok": False, "reason": "missing_cloudflare_api_token"}, 2)
    return t

def api(method: str, path: str, payload=None, content_type: str = "application/json"):
    data = None
    headers = {"Authorization": f"Bearer {token()}"}
    if payload is not None:
        if isinstance(payload, (bytes, bytearray)):
            data = bytes(payload)
        elif content_type == "application/json":
            data = json.dumps(payload).encode()
        else:
            data = str(payload).encode()
        headers["Content-Type"] = content_type
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read().decode("utf-8", "replace")
            return json.loads(body) if body else {"success": True}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"success": False, "raw": body[:4000]}
        return {"success": False, "http_status": exc.code, "cloudflare": parsed}
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}

def zone_id_for(name: str):
    q = urllib.parse.urlencode({"name": name})
    res = api("GET", f"/zones?{q}")
    if not res.get("success"):
        return None, res
    items = res.get("result") or []
    return (items[0].get("id") if items else None), res
