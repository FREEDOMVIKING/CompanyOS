from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path.home() / "companyos"
HOST, PORT = "127.0.0.1", 8768

RUNTIME_ROOTS = [
    ROOT / ".companyos_runtime",
    ROOT / "companyos_runtime",
    ROOT / "runtime",
]

EVENT_FILES = [
    ROOT / "companyos_runtime" / "full_autonomy_journal.jsonl",
    ROOT / ".companyos_runtime" / "full_autonomy_journal.jsonl",
    ROOT / "companyos_runtime" / "ceo_orchestration_journal.jsonl",
    ROOT / ".companyos_runtime" / "ceo_orchestration_journal.jsonl",
    ROOT / "companyos_runtime" / "canonical_production" / "journal.jsonl",
    ROOT / ".companyos_runtime" / "canonical_production" / "journal.jsonl",
    ROOT / ".companyos_runtime" / "productive_autonomy_watchdog.log",
    ROOT / ".companyos_runtime" / "companyos_full_autonomy.log",
    ROOT / "companyos_runtime" / "companyos_full_autonomy.log",
]

STATE_FILES = [
    ROOT / ".companyos_runtime" / "productive_autonomy_watchdog_state.json",
    ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
    ROOT / ".companyos_runtime" / "autonomous_ceo_runtime_service.json",
    ROOT / "companyos_runtime" / "canonical_company" / "runtime_state.json",
    ROOT / ".companyos_runtime" / "canonical_company" / "runtime_state.json",
    ROOT / ".companyos_runtime" / "venture_identity_progression.json",
    ROOT / ".companyos_runtime" / "stalled_stage_progression_state.json",
]

OUTPUT_ROOTS = [
    ROOT / "workspace",
    ROOT / "exports",
    ROOT / "artifacts",
    ROOT / "products",
]

def safe_json(path: Path, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return default

def read_jsonl(path: Path, max_lines=600):
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-max_lines:]
    except Exception:
        return []
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
            else:
                out.append({"raw": obj})
        except Exception:
            out.append({"raw": line})
    return out

def normalize_event(obj, source, index=0):
    now = time.time()
    if not isinstance(obj, dict):
        obj = {"raw": obj}

    ts = (
        obj.get("ts")
        or obj.get("timestamp")
        or obj.get("timestamp_unix")
        or obj.get("updated_at_unix")
        or obj.get("created_at_unix")
        or obj.get("started_at_unix")
        or now
    )

    payload = obj.get("payload")
    if isinstance(payload, dict):
        goal = payload.get("goal") or payload.get("goal_text") or payload.get("topic")
        task = payload.get("task") or payload.get("task_name") or payload.get("name")
    else:
        goal = None
        task = None

    event_type = (
        obj.get("event")
        or obj.get("action")
        or obj.get("type")
        or obj.get("state")
        or obj.get("status")
        or "runtime_event"
    )

    summary = (
        obj.get("summary")
        or obj.get("reason")
        or obj.get("message")
        or obj.get("decision")
        or goal
        or task
    )

    oid = (
        obj.get("orchestration_id")
        or obj.get("last_orchestration_id")
        or (payload.get("orchestration_id") if isinstance(payload, dict) else None)
    )

    return {
        "ts": ts,
        "event_type": str(event_type),
        "summary": str(summary) if summary is not None else None,
        "orchestration_id": oid,
        "source": source,
        "raw": obj,
        "_key": f"{source}:{index}:{oid}:{event_type}:{summary}",
    }

def parse_log_events(path: Path, max_lines=500):
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-max_lines:]
    except Exception:
        return []

    events = []
    for i, line in enumerate(lines):
        text = line.strip()
        if not text:
            continue
        event_type = None
        if "STALLED_STAGE_AUTOSTART" in text:
            event_type = "stalled_stage_autostart"
        elif "AUTOSTART orchestration=" in text:
            event_type = "autostart"
        elif "autostart_failed" in text:
            event_type = "autostart_failed"
        elif "ERROR" in text or "Traceback" in text:
            event_type = "error"
        elif "COMPLETED" in text or '"completed_orchestrations"' in text:
            event_type = "runtime_progress"

        if event_type:
            events.append({
                "ts": path.stat().st_mtime,
                "event_type": event_type,
                "summary": text[:1200],
                "orchestration_id": None,
                "source": str(path.relative_to(ROOT)),
                "raw": {"line": text},
                "_key": f"{path}:{i}:{text[:200]}",
            })
    return events

def collect_events():
    events = []
    for path in EVENT_FILES:
        if not path.exists():
            continue
        rel = str(path.relative_to(ROOT))
        if path.suffix == ".jsonl":
            rows = read_jsonl(path)
            for i, row in enumerate(rows):
                events.append(normalize_event(row, rel, i))
        else:
            events.extend(parse_log_events(path))

    # Also include recently modified JSON state files as state-change events.
    for path in STATE_FILES:
        if not path.exists():
            continue
        obj = safe_json(path, {})
        ev = normalize_event(obj, str(path.relative_to(ROOT)), 0)
        ev["event_type"] = "state_snapshot"
        ev["ts"] = path.stat().st_mtime
        events.append(ev)

    # De-duplicate conservatively.
    dedup = {}
    for e in events:
        key = e.get("_key")
        dedup[key] = e

    rows = list(dedup.values())
    def ts_num(x):
        try:
            return float(x.get("ts") or 0)
        except Exception:
            return 0.0
    rows.sort(key=ts_num, reverse=True)
    return rows[:500]

def latest_runtime():
    candidates = [
        ROOT / "companyos_runtime" / "autonomous_ceo_runtime_service.json",
        ROOT / ".companyos_runtime" / "autonomous_ceo_runtime_service.json",
        ROOT / "companyos_runtime" / "canonical_company" / "runtime_state.json",
        ROOT / ".companyos_runtime" / "canonical_company" / "runtime_state.json",
    ]
    merged = {}
    sources = []
    for p in candidates:
        if p.exists():
            obj = safe_json(p, {})
            if isinstance(obj, dict):
                merged.update(obj)
                sources.append(str(p.relative_to(ROOT)))
    return {"state": merged, "sources": sources}

def watchdog_state():
    p = ROOT / ".companyos_runtime" / "productive_autonomy_watchdog_state.json"
    return safe_json(p, {}) if p.exists() else {}

def lifecycle_state():
    out = {}
    for name in [
        "venture_identity_progression.json",
        "stalled_stage_progression_state.json",
        "diversified_opportunity_governor.json",
    ]:
        p = ROOT / ".companyos_runtime" / name
        if p.exists():
            out[name] = safe_json(p, {})
    return out

def collect_outputs(limit=120):
    rows = []
    for root in OUTPUT_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            try:
                rows.append({
                    "path": str(p.relative_to(ROOT)),
                    "mtime": p.stat().st_mtime,
                    "size": p.stat().st_size,
                })
            except Exception:
                pass
    rows.sort(key=lambda x: x["mtime"], reverse=True)
    return rows[:limit]

def source_health():
    rows = []
    for p in EVENT_FILES + STATE_FILES:
        if p.exists():
            rows.append({
                "path": str(p.relative_to(ROOT)),
                "mtime": p.stat().st_mtime,
                "size": p.stat().st_size,
            })
    rows.sort(key=lambda x: x["mtime"], reverse=True)
    return rows

def summarize():
    events = collect_events()
    runtime = latest_runtime()
    ws = watchdog_state()
    outputs = collect_outputs()
    now = time.time()

    completed = runtime["state"].get("completed_orchestrations", 0) or 0
    active = runtime["state"].get("active_orchestrations", 0) or 0
    failures = runtime["state"].get("failed_orchestrations", 0) or 0
    autostarts = ws.get("total_autostarts", 0) or 0

    recent_events = [e for e in events if (now - float(e.get("ts") or now)) <= 900]
    score = min(
        100,
        int(completed) * 4
        + int(autostarts) * 6
        + min(20, len(outputs))
        + min(20, len(recent_events)),
    )

    return {
        "generated_at_unix": now,
        "runtime": runtime,
        "watchdog": ws,
        "lifecycle": lifecycle_state(),
        "events": events,
        "outputs": outputs,
        "source_health": source_health(),
        "summary": {
            "completed_orchestrations": completed,
            "active_orchestrations": active,
            "failed_orchestrations": failures,
            "total_autostarts": autostarts,
            "recent_events_15m": len(recent_events),
            "observed_productive_activity_score": score,
        }
    }

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/ledger":
            self.send_json(summarize())
            return
        if path == "/api/health":
            self.send_json({"ok": True, "time": time.time(), "sources": source_health()})
            return
        if path == "/":
            html = Path(__file__).with_name("autonomy_activity_ledger.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        self.send_json({"ok": False, "error": "not found"}, 404)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    print(f"CompanyOS Live Autonomy Activity Ledger started: http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
