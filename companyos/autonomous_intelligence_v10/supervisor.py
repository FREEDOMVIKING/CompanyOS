import subprocess, sys, time
from pathlib import Path
from .core import now

HOME=Path.home()/"companyos"
RUN=HOME/".companyos_enterprise_v10"
RUN.mkdir(parents=True,exist_ok=True)
STOP=RUN/"supervisor.stop"
RUNTIME_PID=RUN/"runtime.pid"
STATE=RUN/"supervisor_status.json"

def write_state(status,pid=None,restarts=0):
    import json
    STATE.write_text(json.dumps({"status":status,"runtime_pid":pid,"restart_count":restarts,"updated_at":now()},indent=2))

def main():
    if STOP.exists(): STOP.unlink()
    restarts=0
    child=None
    while not STOP.exists():
        if child is None or child.poll() is not None:
            if child is not None: restarts += 1
            log=open(RUN/"v10.log","ab",buffering=0)
            child=subprocess.Popen(
                [sys.executable,"-u","-m","companyos.autonomous_intelligence_v10.server"],
                cwd=str(HOME),stdout=log,stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,start_new_session=True
            )
            RUNTIME_PID.write_text(str(child.pid))
            write_state("running",child.pid,restarts)
        time.sleep(5)
    if child and child.poll() is None:
        try: child.terminate()
        except Exception: pass
    write_state("stopped",None,restarts)

if __name__=="__main__":
    main()
