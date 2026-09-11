from __future__ import annotations
import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path.home() / "companyos"
HOST, PORT = "127.0.0.1", 8767

SEARCH_ROOTS = [
    ROOT / "companyos_runtime",
    ROOT / ".companyos_runtime",
    ROOT / "ceo_memory",
    ROOT / "runtime",
]

SKIP_PARTS = ("/backups/", "/.git/", "/__pycache__/")

def safe_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None

def text_of(obj):
    try:
        return json.dumps(obj, default=str).lower()
    except Exception:
        return str(obj).lower()

def find_json_files():
    seen = set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.json"):
            s = str(p)
            if any(x in s for x in SKIP_PARTS):
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p

def find_jsonl_files():
    seen = set()
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.jsonl"):
            s = str(p)
            if any(x in s for x in SKIP_PARTS):
                continue
            if p in seen:
                continue
            seen.add(p)
            yield p

def collect_matches(subject: str):
    needle = subject.lower().strip()
    matches = []
    for p in find_json_files():
        obj = safe_json(p)
        if obj is None:
            continue
        if needle and needle not in text_of(obj):
            continue
        matches.append({
            "path": str(p.relative_to(ROOT)),
            "mtime": p.stat().st_mtime,
            "data": obj,
        })
    # journal-style line matches
    for p in find_jsonl_files():
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()[-500:]
        except Exception:
            continue
        hit_lines = []
        for line in lines:
            if needle and needle not in line.lower():
                continue
            try:
                hit_lines.append(json.loads(line))
            except Exception:
                pass
        if hit_lines:
            matches.append({
                "path": str(p.relative_to(ROOT)),
                "mtime": p.stat().st_mtime,
                "data": hit_lines[-50:],
            })
    return matches

def flatten_items(obj):
    out = []
    if isinstance(obj, dict):
        out.append(obj)
        for v in obj.values():
            out.extend(flatten_items(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(flatten_items(v))
    return out

def infer_progress(subject: str):
    matches = collect_matches(subject)
    all_items = []
    for m in matches:
        all_items.extend(flatten_items(m["data"]))

    completed = []
    active = []
    queued = []
    blocked = []
    approvals = []
    evidence = []
    milestones = []
    latest_ts = 0.0

    def add_unique(lst, value):
        s = str(value).strip()
        if s and s not in lst:
            lst.append(s)

    for d in all_items:
        if not isinstance(d, dict):
            continue
        blob = text_of(d)
        status = str(d.get("status") or d.get("state") or d.get("decision") or "").upper()
        name = d.get("name") or d.get("title") or d.get("task") or d.get("goal") or d.get("topic") or d.get("action")
        reason = d.get("reason") or d.get("last_error") or d.get("blocker")

        if status in ("COMPLETED","DONE","SUCCESS","SUCCEEDED","FINALIZED"):
            add_unique(completed, name or d.get("summary") or status)
        elif status in ("RUNNING","EXECUTING","ACTIVE","IN_PROGRESS"):
            add_unique(active, name or d.get("summary") or status)
        elif status in ("QUEUED","PENDING","READY","PLANNED"):
            add_unique(queued, name or d.get("summary") or status)
        elif status in ("BLOCKED","FAILED","HALTED","REJECTED"):
            add_unique(blocked, f"{name or status}: {reason or status}")

        if "approval" in blob and ("pending" in blob or "await" in blob or d.get("requires_approval")):
            add_unique(approvals, name or d.get("summary") or d.get("decision_id") or "Approval pending")

        if any(k in d for k in ("evidence","research","sources","validation_score","score")):
            add_unique(evidence, d.get("summary") or d.get("evidence") or d.get("research") or name or "Evidence/research record")

        if any(k in d for k in ("milestone","stage","phase","current_stage")):
            add_unique(milestones, d.get("milestone") or d.get("stage") or d.get("phase") or d.get("current_stage"))

        for k in ("updated_at_unix","last_cycle_unix","created_at_unix","ts","timestamp"):
            v = d.get(k)
            try:
                if isinstance(v,(int,float)):
                    latest_ts = max(latest_ts,float(v))
            except Exception:
                pass

    # conservative progress estimate based only on observed state, not fake business KPIs
    total = len(completed) + len(active) + len(queued) + len(blocked)
    if total:
        pct = round((len(completed) + 0.5*len(active)) / total * 100)
    else:
        pct = None

    current_stage = active[0] if active else (queued[0] if queued else (completed[-1] if completed else "No active work detected"))

    return {
        "subject": subject,
        "current_stage": current_stage,
        "observed_progress_percent": pct,
        "completed": completed[:50],
        "active": active[:50],
        "queued": queued[:50],
        "blocked": blocked[:50],
        "approvals": approvals[:50],
        "evidence": evidence[:50],
        "milestones": milestones[:50],
        "latest_activity_unix": latest_ts or None,
        "sources": [{"path":m["path"],"mtime":m["mtime"]} for m in sorted(matches,key=lambda x:x["mtime"], reverse=True)[:40]],
        "note": "Progress percentage is derived from observed task states only. It is not a fabricated business-completion estimate."
    }

class H(BaseHTTPRequestHandler):
    def send_json(self,obj,code=200):
        b=json.dumps(obj,indent=2,default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=="/":
            b=Path(__file__).with_name("venture_progress.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if u.path=="/api/progress":
            q=parse_qs(u.query)
            subject=(q.get("subject") or ["digital template business"])[0]
            self.send_json(infer_progress(subject))
            return
        self.send_json({"ok":False,"error":"not found"},404)
    def log_message(self,*args): pass

if __name__=="__main__":
    print(f"CompanyOS Venture Progress Tracker started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
