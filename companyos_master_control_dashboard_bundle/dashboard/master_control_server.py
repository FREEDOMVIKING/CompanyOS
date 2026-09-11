import json, os, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path.home() / "companyos"
HOST, PORT = "127.0.0.1", 8766

ALLOWED = {
    "autonomy_status": ["bash", "scripts/companyos_full_autonomy.sh", "status"],
    "autonomy_start": ["bash", "scripts/companyos_full_autonomy.sh", "start"],
    "autonomy_stop": ["bash", "scripts/companyos_full_autonomy.sh", "stop"],
    "autonomy_restart": ["bash", "scripts/companyos_full_autonomy.sh", "restart"],
    "final_status": ["python", "scripts/companyos_final_launch.py", "status"],
    "final_preflight": ["python", "scripts/companyos_final_launch.py", "preflight"],
    "final_safe": ["python", "scripts/companyos_final_launch.py", "safe"],
    "full_check": ["bash", "scripts/companyos_final_start.sh", "full-check"],
    "dashboard_status": ["bash", "-lc", "ss -ltn 2>/dev/null | grep -E ':8765|:8766' || true"],
}

def run(cmd, timeout=20):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
    p = subprocess.run(cmd, cwd=ROOT, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=timeout, check=False)
    return {"ok": p.returncode == 0, "code": p.returncode, "output": p.stdout[-20000:]}

def live_profile(payload):
    mode = payload.get("mode")
    if mode == "safe":
        return run(["python","scripts/companyos_final_launch.py","safe"])
    if mode == "trial":
        token = payload.get("confirm","")
        if token != "I_UNDERSTAND_TRIAL_LIVE":
            return {"ok":False,"code":2,"output":"Confirmation token incorrect."}
        return run(["python","scripts/companyos_final_launch.py","trial",
                    "--max-single",str(payload.get("max_single","0.01")),
                    "--max-daily",str(payload.get("max_daily","0.05")),
                    "--confirm",token])
    if mode == "full":
        token = payload.get("confirm","")
        if token != "I_UNDERSTAND_FULL_LIVE":
            return {"ok":False,"code":2,"output":"Confirmation token incorrect."}
        return run(["python","scripts/companyos_final_launch.py","full",
                    "--max-single",str(payload.get("max_single","0.01")),
                    "--max-daily",str(payload.get("max_daily","0.05")),
                    "--max-failures",str(payload.get("max_failures","2")),
                    "--confirm",token])
    return {"ok":False,"code":2,"output":"Unknown profile mode."}

def snapshot():
    out = {}
    for key in ("autonomy_status","final_status","dashboard_status"):
        try: out[key] = run(ALLOWED[key], 10)
        except Exception as e: out[key] = {"ok":False,"output":f"{type(e).__name__}: {e}"}
    for p in [ROOT/"companyos_runtime"/"launch_controller_state.json",
              ROOT/".companyos_runtime"/"launch_controller_state.json"]:
        if p.exists():
            try:
                out["gateway_state"] = json.loads(p.read_text())
                break
            except Exception:
                pass
    return out

class H(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        data = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/":
            data = Path(__file__).with_name("master_control.html").read_bytes()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p == "/api/snapshot": self.send_json(snapshot()); return
        if p == "/api/logs":
            log = ROOT/".companyos_runtime"/"companyos_full_autonomy.log"
            txt = log.read_text(errors="ignore")[-25000:] if log.exists() else "No autonomy log found."
            self.send_json({"ok":True,"output":txt}); return
        self.send_json({"ok":False,"error":"not found"},404)
    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length","0") or 0)
        payload = {}
        if n:
            try: payload = json.loads(self.rfile.read(n))
            except Exception: pass
        if p == "/api/action":
            a = payload.get("action")
            if a not in ALLOWED: self.send_json({"ok":False,"output":"Action not allowed."},400); return
            try: self.send_json(run(ALLOWED[a]))
            except Exception as e: self.send_json({"ok":False,"output":f"{type(e).__name__}: {e}"},500)
            return
        if p == "/api/live-profile":
            try: self.send_json(live_profile(payload))
            except Exception as e: self.send_json({"ok":False,"output":f"{type(e).__name__}: {e}"},500)
            return
        self.send_json({"ok":False,"error":"not found"},404)
    def log_message(self, *args): pass

if __name__ == "__main__":
    print(f"CompanyOS Master Control Center started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
