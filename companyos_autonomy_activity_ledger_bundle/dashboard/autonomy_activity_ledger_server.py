from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path.home() / "companyos"
HOST, PORT = "127.0.0.1", 8768

def safe_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}

def read_runtime():
    for p in [
        ROOT/"companyos_runtime"/"autonomous_ceo_runtime_service.json",
        ROOT/".companyos_runtime"/"autonomous_ceo_runtime_service.json",
    ]:
        if p.exists():
            return safe_json(p)
    return {}

def recent_autostarts(limit=20):
    p=ROOT/".companyos_runtime"/"productive_autonomy_watchdog.log"
    if not p.exists(): return []
    rows=[]
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()[-1000:]:
        if "AUTOSTART orchestration=" in line:
            rows.append(line.strip())
    return rows[-limit:]

def recent_journal(limit=80):
    candidates=[
        ROOT/"companyos_runtime"/"ceo_orchestration_journal.jsonl",
        ROOT/".companyos_runtime"/"ceo_orchestration_journal.jsonl",
    ]
    for p in candidates:
        if p.exists():
            out=[]
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()[-1000:]:
                try: out.append(json.loads(line))
                except Exception: pass
            return out[-limit:]
    return []

def task_summary(limit=100):
    roots=[ROOT/".companyos_runtime"/"task_queue",ROOT/"companyos_runtime"/"task_queue"]
    rows=[]
    for q in roots:
        if not q.exists(): continue
        for p in sorted(q.glob("*.json"), key=lambda x:x.stat().st_mtime, reverse=True)[:limit]:
            obj=safe_json(p)
            if obj:
                obj["_file"]=p.name
                rows.append(obj)
    return rows[:limit]

def outputs(limit=100):
    roots=[ROOT/"workspace",ROOT/"exports",ROOT/"artifacts",ROOT/"products"]
    rows=[]
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if p.is_file():
                try:
                    rows.append({"path":str(p.relative_to(ROOT)),"mtime":p.stat().st_mtime,"size":p.stat().st_size})
                except Exception: pass
    rows.sort(key=lambda x:x["mtime"], reverse=True)
    return rows[:limit]

def snapshot():
    ws_path=ROOT/".companyos_runtime"/"productive_autonomy_watchdog_state.json"
    ws=safe_json(ws_path) if ws_path.exists() else {}
    rt=read_runtime()
    journal=recent_journal()
    tasks=task_summary()

    active=[]; completed=[]; failed=[]
    for t in tasks:
        s=str(t.get("status") or t.get("state") or "").upper()
        row={
            "task_id":t.get("task_id") or t.get("id") or t.get("_file"),
            "name":t.get("name") or t.get("goal") or t.get("topic") or t.get("task_type"),
            "assigned_agent":t.get("assigned_agent"),
            "status":s,
            "summary":t.get("summary") or t.get("result") or t.get("last_error"),
        }
        if s in ("RUNNING","EXECUTING","ACTIVE","IN_PROGRESS"): active.append(row)
        elif s in ("COMPLETED","DONE","SUCCESS","SUCCEEDED"): completed.append(row)
        elif s in ("FAILED","BLOCKED","HALTED","REJECTED"): failed.append(row)

    goals=[]
    for e in journal[-100:]:
        if isinstance(e,dict):
            payload=e.get("payload")
            if isinstance(payload,dict):
                g=payload.get("goal") or payload.get("goal_text") or payload.get("topic")
                if g and g not in goals: goals.append(g)

    outs=outputs()
    score=min(100,
        min(40,int(rt.get("completed_orchestrations",0) or 0)*5)
        + min(25,len(completed)*3)
        + min(20,len(outs)*2)
        + (15 if int(ws.get("total_autostarts",0) or 0)>0 else 0)
    )

    return {
        "watchdog":ws,
        "runtime":rt,
        "autostarts":recent_autostarts(),
        "recent_goals":goals[-20:],
        "active_tasks":active[:50],
        "completed_tasks":completed[:50],
        "failed_tasks":failed[:50],
        "recent_journal":journal[-50:],
        "outputs":outs[:50],
        "business_progress_score":score,
        "note":"This is an observed activity/progress signal from orchestrations, tasks, and generated outputs. It is not a revenue or profitability metric."
    }

class H(BaseHTTPRequestHandler):
    def send_json(self,obj,code=200):
        b=json.dumps(obj,indent=2,default=str).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=="/":
            b=Path(__file__).with_name("autonomy_activity_ledger.html").read_bytes()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b); return
        if u.path=="/api/ledger":
            self.send_json(snapshot()); return
        self.send_json({"ok":False,"error":"not found"},404)
    def log_message(self,*args): pass

if __name__=="__main__":
    print(f"CompanyOS Autonomy Activity Ledger started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
