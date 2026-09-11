#!/usr/bin/env python3
import json, os, signal, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "companyos"
STATE = ROOT / ".companyos_runtime" / "supervisor_v4"
PID_DIR = STATE / "pids"
LOG_DIR = STATE / "logs"
STATE_FILE = STATE / "state.json"
EVENTS = STATE / "events.jsonl"
INTERVAL = int(os.environ.get("COMPANYOS_SUPERVISOR_INTERVAL", "20"))
running = True

SERVICES = {
    "master_control": ("dashboard/master_control_server.py", 8766),
    "venture_progress": ("dashboard/venture_progress_v2_server.py", 8767),
    "activity_ledger": ("dashboard/autonomy_activity_ledger_server.py", 8768),
}

def now(): return datetime.now(timezone.utc).isoformat()

def emit(message, **extra):
    row={"at":now(),"message":message,**extra}
    LOG_DIR.mkdir(parents=True,exist_ok=True)
    with EVENTS.open("a",encoding="utf-8") as f:f.write(json.dumps(row,sort_keys=True)+"\n")
    with (LOG_DIR/"supervisor.log").open("a",encoding="utf-8") as f:f.write(json.dumps(row,sort_keys=True)+"\n")
    print(json.dumps(row,sort_keys=True),flush=True)

def alive(pid):
    try: os.kill(int(pid),0); return True
    except Exception: return False

def cmdline(pid):
    try:return Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0",b" ").decode(errors="ignore")
    except Exception:return ""

def find(fragment):
    try: out=subprocess.check_output(["ps","-ef"],text=True,errors="ignore")
    except Exception:return None
    for line in out.splitlines():
        if fragment in line and "grep" not in line and "supervisor_v4.py" not in line:
            parts=line.split()
            if len(parts)>1 and parts[1].isdigit(): return int(parts[1])
    return None

def http_ok(port):
    try:
        return subprocess.run(
            ["curl","-fsS","--max-time","3",f"http://127.0.0.1:{port}"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5
        ).returncode==0
    except Exception:return False

def ensure_dashboard(name, rel, port):
    script=ROOT/rel
    pidfile=PID_DIR/f"{name}.pid"
    pid=None
    try: pid=int(pidfile.read_text().strip())
    except Exception: pass

    if pid and alive(pid) and script.name in cmdline(pid) and http_ok(port):
        return {"status":"running","pid":pid,"port":port}

    existing=find(script.name)
    if existing and http_ok(port):
        pidfile.write_text(str(existing),encoding="utf-8")
        emit("adopted dashboard",service=name,pid=existing,port=port)
        return {"status":"running","pid":existing,"port":port}

    if not script.exists():
        emit("dashboard script missing",service=name,script=str(script))
        return {"status":"missing","port":port}

    logfile=LOG_DIR/f"{name}.log"
    with logfile.open("ab") as out:
        proc=subprocess.Popen(
            [sys.executable,"-u",str(script)],cwd=ROOT,
            stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,
            start_new_session=True
        )
    pidfile.write_text(str(proc.pid),encoding="utf-8")
    time.sleep(1.5)
    ok=alive(proc.pid) and http_ok(port)
    emit("dashboard started" if ok else "dashboard failed",service=name,pid=proc.pid,port=port)
    return {"status":"running" if ok else "failed","pid":proc.pid,"port":port}

def runtime_count():
    try: out=subprocess.check_output(["ps","-ef"],text=True,errors="ignore")
    except Exception:return 0
    return sum(
        1 for line in out.splitlines()
        if "python" in line and ("-m companyos." in line or "companyos_daemon" in line)
        and "grep" not in line and "supervisor_v4.py" not in line
    )

def recover_runtime():
    count=runtime_count()
    if count>0:return {"status":"running","process_count":count}
    ctl=ROOT/"companyosctl"
    if not ctl.exists():return {"status":"missing_ctl","process_count":0}
    emit("CompanyOS runtime absent; starting")
    try:
        cp=subprocess.run(["bash",str(ctl),"start"],cwd=ROOT,text=True,capture_output=True,timeout=180)
        emit("CompanyOS start finished",returncode=cp.returncode,stdout=cp.stdout[-1000:],stderr=cp.stderr[-1000:])
    except Exception as exc:
        emit("CompanyOS start failed",error=str(exc))
    return {"status":"recovery_attempted","process_count":runtime_count()}

def cycle():
    PID_DIR.mkdir(parents=True,exist_ok=True);LOG_DIR.mkdir(parents=True,exist_ok=True)
    runtime=recover_runtime()
    dashboards={name:ensure_dashboard(name,rel,port) for name,(rel,port) in SERVICES.items()}
    STATE_FILE.write_text(json.dumps({
        "generated_at":now(),"supervisor_pid":os.getpid(),
        "runtime":runtime,"dashboards":dashboards
    },indent=2,sort_keys=True),encoding="utf-8")

def stop(*_):
    global running
    running=False

def main():
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    emit("Runtime Supervisor V4 started",pid=os.getpid(),interval=INTERVAL)
    while running:
        try:cycle()
        except Exception as exc:emit("supervisor cycle error",error=str(exc))
        for _ in range(INTERVAL):
            if not running:break
            time.sleep(1)
    emit("Runtime Supervisor V4 stopped",pid=os.getpid())

if __name__=="__main__":main()
