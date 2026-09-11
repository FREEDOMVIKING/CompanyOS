from __future__ import annotations
import json,re,time
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path.home()/"companyos"
HOST,PORT="127.0.0.1",8768
EVENT_FILES=[
 ROOT/"companyos_runtime/full_autonomy_journal.jsonl",
 ROOT/".companyos_runtime/full_autonomy_journal.jsonl",
 ROOT/"companyos_runtime/ceo_orchestration_journal.jsonl",
 ROOT/".companyos_runtime/ceo_orchestration_journal.jsonl",
 ROOT/".companyos_runtime/productive_autonomy_watchdog.log",
 ROOT/".companyos_runtime/companyos_full_autonomy.log",
 ROOT/"companyos_runtime/companyos_full_autonomy.log",
]
STATE_FILES=[
 ROOT/".companyos_runtime/productive_autonomy_watchdog_state.json",
 ROOT/"companyos_runtime/autonomous_ceo_runtime_service.json",
 ROOT/".companyos_runtime/autonomous_ceo_runtime_service.json",
]
OUTPUT_ROOTS=[ROOT/"workspace",ROOT/"exports",ROOT/"artifacts",ROOT/"products"]
LOG_TS=re.compile(r'^(?P<date>\\d{4}-\\d{2}-\\d{2})[ T](?P<time>\\d{2}:\\d{2}:\\d{2})(?:\\.(?P<frac>\\d+))?')

def safe_json(path,default=None):
    if default is None: default={}
    try:return json.loads(path.read_text(encoding="utf-8",errors="ignore"))
    except Exception:return default

def parse_log_timestamp(line,fallback):
    m=LOG_TS.search(line.strip())
    if not m:return fallback
    frac=(m.group("frac") or "0")
    frac=(frac+"000000")[:6]
    raw=f"{m.group('date')} {m.group('time')}.{frac}"
    try:return datetime.strptime(raw,"%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()
    except Exception:return fallback

def classify_log_line(text):
    low=text.lower()
    if "stalled_stage_autostart" in low:return "stalled_stage_autostart"
    if "autostart orchestration=" in low:return "autostart"
    if "autostart_failed" in low:return "autostart_failed"
    if "traceback" in low or "typeerror" in low or "error " in low:return "error"
    if "completed" in low or '"completed_orchestrations"' in low:return "runtime_progress"
    return None

def parse_log_events(path,max_lines=1200):
    if not path.exists():return []
    try:
        lines=path.read_text(encoding="utf-8",errors="ignore").splitlines()[-max_lines:]
        fallback=path.stat().st_mtime
    except Exception:return []
    out=[]
    for line in lines:
        text=line.strip()
        if not text:continue
        typ=classify_log_line(text)
        if not typ:continue
        out.append({"ts":parse_log_timestamp(text,fallback),"event_type":typ,"summary":text[:1600],"source":str(path.relative_to(ROOT)),"orchestration_id":None})
    return out

def read_jsonl(path,max_lines=800):
    if not path.exists():return []
    try:lines=path.read_text(encoding="utf-8",errors="ignore").splitlines()[-max_lines:]
    except Exception:return []
    out=[]
    for line in lines:
        line=line.strip()
        if not line:continue
        try:obj=json.loads(line)
        except Exception:obj={"raw":line}
        if not isinstance(obj,dict):obj={"raw":obj}
        payload=obj.get("payload") if isinstance(obj.get("payload"),dict) else {}
        ts=obj.get("ts") or obj.get("timestamp_unix") or obj.get("updated_at_unix") or obj.get("created_at_unix") or obj.get("started_at_unix") or path.stat().st_mtime
        typ=obj.get("event") or obj.get("action") or obj.get("type") or obj.get("state") or obj.get("status") or "runtime_event"
        summary=obj.get("summary") or obj.get("reason") or obj.get("message") or obj.get("decision") or payload.get("goal") or payload.get("goal_text") or payload.get("topic")
        oid=obj.get("orchestration_id") or obj.get("last_orchestration_id") or payload.get("orchestration_id")
        try:ts=float(ts)
        except Exception:ts=path.stat().st_mtime
        out.append({"ts":ts,"event_type":str(typ),"summary":str(summary) if summary is not None else None,"source":str(path.relative_to(ROOT)),"orchestration_id":oid})
    return out

def canonical_key(e):
    summary=(e.get("summary") or "").strip()
    summary=re.sub(r'\\b\\d{4}-\\d{2}-\\d{2}[ T]\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?\\b','',summary)
    summary=re.sub(r'"ts"\\s*:\\s*\\d+(?:\\.\\d+)?','"ts":X',summary)
    summary=re.sub(r'"cycle_count"\\s*:\\s*\\d+','"cycle_count":X',summary)
    summary=re.sub(r'\\s+',' ',summary).strip()[:500]
    return (e.get("event_type"),e.get("orchestration_id"),summary)

def collect_events():
    events=[]
    for p in EVENT_FILES:
        if not p.exists():continue
        events.extend(read_jsonl(p) if p.suffix==".jsonl" else parse_log_events(p))
    grouped={}
    for e in sorted(events,key=lambda x:float(x.get("ts") or 0),reverse=True):
        k=canonical_key(e)
        if k not in grouped:
            e["repeat_count"]=1;grouped[k]=e
        else:
            grouped[k]["repeat_count"]+=1
    rows=list(grouped.values())
    rows.sort(key=lambda x:float(x.get("ts") or 0),reverse=True)
    return rows[:500]

def runtime_state():
    merged={}
    for p in STATE_FILES:
        if p.exists():
            o=safe_json(p,{})
            if isinstance(o,dict):merged.update(o)
    return merged

def outputs(limit=120):
    rows=[]
    for r in OUTPUT_ROOTS:
        if not r.exists():continue
        for p in r.rglob("*"):
            if p.is_file():
                try:rows.append({"path":str(p.relative_to(ROOT)),"mtime":p.stat().st_mtime,"size":p.stat().st_size})
                except Exception:pass
    rows.sort(key=lambda x:x["mtime"],reverse=True)
    return rows[:limit]

def summarize():
    now=time.time();events=collect_events();rt=runtime_state()
    recent=[e for e in events if 0<=now-float(e.get("ts") or now)<=900]
    current_errors=[e for e in recent if e.get("event_type") in ("error","autostart_failed")]
    history=[e for e in events if e.get("event_type") in ("error","autostart_failed") and now-float(e.get("ts") or 0)>900][:50]
    return {
      "generated_at_unix":now,
      "summary":{"completed_orchestrations":rt.get("completed_orchestrations",0) or 0,"active_orchestrations":rt.get("active_orchestrations",0) or 0,"failed_orchestrations":rt.get("failed_orchestrations",0) or 0,"recent_events_15m":len(recent),"current_errors_15m":len(current_errors)},
      "current_events":events[:150],
      "current_errors":current_errors,
      "historical_errors":history,
      "outputs":outputs(),
      "runtime":rt
    }

HTML=Path(__file__).with_name("autonomy_activity_ledger.html")
class H(BaseHTTPRequestHandler):
    def send_json(self,obj,code=200):
        b=json.dumps(obj,indent=2,default=str).encode()
        self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store, no-cache, must-revalidate, max-age=0");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/api/ledger":self.send_json(summarize());return
        if p=="/":
            b=HTML.read_bytes();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Cache-Control","no-store, no-cache, must-revalidate, max-age=0");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b);return
        self.send_json({"ok":False,"error":"not found"},404)
    def log_message(self,*args):pass
if __name__=="__main__":
    print(f"CompanyOS Ledger timestamp/dedupe fix active: http://{HOST}:{PORT}",flush=True)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
