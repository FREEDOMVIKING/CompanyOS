from __future__ import annotations

import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path.home() / "companyos"
HOST, PORT = "127.0.0.1", 8767

def run(cmd, timeout=12):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
    p = subprocess.run(
        cmd, cwd=ROOT, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout, check=False,
    )
    return {"ok": p.returncode == 0, "code": p.returncode, "output": p.stdout}

def load_dashboard_snapshot():
    # Prefer the same local API the executive dashboard uses.
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/dashboard", timeout=4) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        pass

    # Fallback: import dashboard builder directly if available.
    try:
        import importlib.util
        p = ROOT / "dashboard" / "server.py"
        spec = importlib.util.spec_from_file_location("_companyos_dashboard_server", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in ("dashboard_data", "build_dashboard", "get_dashboard", "snapshot", "dashboard_snapshot"):
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn()
    except Exception:
        pass
    return {}

def safe_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None

def normalize_subject(s: str):
    return " ".join((s or "").strip().lower().split())

def text_blob(obj):
    try:
        return json.dumps(obj, default=str).lower()
    except Exception:
        return str(obj).lower()

def collect_runtime_records(subject: str):
    needle = normalize_subject(subject)
    roots = [
        ROOT / ".companyos_runtime",
        ROOT / "companyos_runtime",
        ROOT / "ceo_memory",
        ROOT / "runtime",
    ]
    records = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.json"):
            sp = str(p)
            if any(x in sp for x in ("/backups/", "/.git/", "/__pycache__/")):
                continue
            obj = safe_json(p)
            if obj is None:
                continue
            blob = text_blob(obj)
            if needle and needle not in blob:
                continue
            records.append((p, obj))
    return records

def flatten(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from flatten(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from flatten(v)

def related(item, subject):
    blob = text_blob(item)
    needle = normalize_subject(subject)
    if needle and needle in blob:
        return True
    # tolerate common dashboard label variations
    words = [w for w in needle.split() if len(w) >= 4]
    return bool(words) and sum(1 for w in words if w in blob) >= max(1, len(words)-1)

def derive(subject: str):
    snap = load_dashboard_snapshot() or {}
    portfolio = snap.get("portfolio") if isinstance(snap, dict) else {}
    if not isinstance(portfolio, dict):
        portfolio = {}

    roadmap = snap.get("roadmap") if isinstance(snap, dict) else None
    if roadmap is None:
        roadmap = portfolio.get("priorities", [])
    if not isinstance(roadmap, list):
        roadmap = []

    decisions = snap.get("decisions", []) if isinstance(snap, dict) else []
    if not isinstance(decisions, list):
        decisions = []

    pending_decisions = snap.get("pending_decisions", []) if isinstance(snap, dict) else []
    if not isinstance(pending_decisions, list):
        pending_decisions = []

    all_decisions = decisions + [d for d in pending_decisions if d not in decisions]

    roadmap_item = None
    for r in roadmap:
        if isinstance(r, dict) and related(r, subject):
            roadmap_item = r
            break

    matching_decisions = [d for d in all_decisions if isinstance(d, dict) and related(d, subject)]

    runtime_records = collect_runtime_records(subject)
    runtime_items = []
    sources = []
    for p, obj in runtime_records:
        sources.append(str(p.relative_to(ROOT)))
        runtime_items.extend(list(flatten(obj)))

    # Pull tasks from dashboard snapshot where available.
    task_buckets = []
    for key in ("tasks", "pending_tasks", "completed_tasks", "failed_tasks"):
        val = snap.get(key) if isinstance(snap, dict) else None
        if isinstance(val, list):
            task_buckets.extend(val)

    related_tasks = [t for t in task_buckets if isinstance(t, dict) and related(t, subject)]
    related_runtime = [x for x in runtime_items if isinstance(x, dict)]

    active, completed, queued, blocked, approvals, evidence, milestones = [], [], [], [], [], [], []

    def add(lst, value):
        if value is None:
            return
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        s = str(value).strip()
        if s and s not in lst:
            lst.append(s)

    def classify(d):
        status = str(d.get("status") or d.get("state") or d.get("decision") or "").upper()
        name = d.get("name") or d.get("title") or d.get("task") or d.get("goal") or d.get("topic") or d.get("action") or d.get("summary")
        reason = d.get("reason") or d.get("last_error") or d.get("blocker")

        if status in ("RUNNING","EXECUTING","ACTIVE","IN_PROGRESS"):
            add(active, name or status)
        elif status in ("COMPLETED","DONE","SUCCESS","SUCCEEDED","FINALIZED"):
            add(completed, name or status)
        elif status in ("QUEUED","PENDING","READY","PLANNED","NEW"):
            add(queued, name or status)
        elif status in ("BLOCKED","FAILED","HALTED","REJECTED"):
            add(blocked, f"{name or status}: {reason or status}")

        blob = text_blob(d)
        if d.get("owner_approval_required") or d.get("requires_approval") or ("approval" in blob and ("pending" in blob or "await" in blob)):
            add(approvals, name or d.get("id") or d.get("decision_id") or "Approval pending")

        if any(k in d for k in ("evidence","research","sources","validation_score","priority_score","score")):
            add(evidence, d.get("summary") or d.get("evidence") or d.get("research") or name or "Research/evidence record")

        for k in ("milestone","stage","phase","current_stage"):
            if d.get(k):
                add(milestones, d.get(k))

    for d in related_tasks + matching_decisions + related_runtime:
        classify(d)

    # Determine a clear current state from real signals.
    if active:
        state = "ACTIVE"
        current = active[0]
    elif approvals:
        state = "AWAITING_APPROVAL"
        current = approvals[0]
    elif blocked:
        state = "BLOCKED"
        current = blocked[0]
    elif queued:
        state = "QUEUED"
        current = queued[0]
    elif roadmap_item:
        action = roadmap_item.get("action") or "review"
        reason = roadmap_item.get("reason") or ""
        state = "ROADMAP_REVIEW"
        current = f"{action}: {reason}".strip(": ")
    else:
        state = "NO_LINKED_WORK"
        current = "No active or queued work linked to this roadmap subject."

    # Conservative observed progress only.
    total = len(active) + len(completed) + len(queued) + len(blocked)
    pct = round((len(completed) + 0.5 * len(active)) / total * 100) if total else None

    # Explicit explanation when roadmap exists but no execution is linked.
    explanation = ""
    if roadmap_item and not (active or queued or blocked or approvals or completed):
        explanation = (
            "This item exists in the Executive Roadmap, but no linked execution task, milestone, "
            "or decision was found yet. The roadmap entry is a ranked recommendation, not proof of active execution."
        )
    elif approvals and not active:
        explanation = "Progress is currently waiting on an approval or decision before execution can continue."
    elif active:
        explanation = "Linked CompanyOS work is currently active."
    elif queued:
        explanation = "Linked work exists and is queued, but no active execution record is currently running."

    return {
        "subject": subject,
        "state": state,
        "current": current,
        "progress_percent": pct,
        "roadmap_item": roadmap_item,
        "active": active[:50],
        "completed": completed[:50],
        "queued": queued[:50],
        "blocked": blocked[:50],
        "approvals": approvals[:50],
        "evidence": evidence[:50],
        "milestones": milestones[:50],
        "matching_decisions": matching_decisions[:20],
        "sources": sorted(set(sources))[:60],
        "explanation": explanation,
        "dashboard_connected": bool(snap),
        "note": "Progress is derived from the same Executive Dashboard snapshot plus linked CompanyOS runtime records. No synthetic business milestones are invented."
    }

class H(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        b = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            b = Path(__file__).with_name("venture_progress_v2.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if u.path == "/api/progress":
            q = parse_qs(u.query)
            subject = (q.get("subject") or ["digital template business"])[0]
            self.send_json(derive(subject))
            return
        self.send_json({"ok":False,"error":"not found"},404)

    def log_message(self,*args):
        pass

if __name__ == "__main__":
    print(f"CompanyOS Venture Progress V2 started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
