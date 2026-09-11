import subprocess, sys, time, json
from pathlib import Path
from .util import now

HOME=Path.home()/"companyos"
RUN=HOME/".companyos_enterprise_v11"
RUN.mkdir(parents=True,exist_ok=True)
STOP=RUN/"supervisor.stop"; PID=RUN/"runtime.pid"; STATE=RUN/"supervisor_status.json"

def state(status,pid=None,restarts=0):
    STATE.write_text(json.dumps({"status":status,"runtime_pid":pid,"restart_count":restarts,"updated_at":now()},indent=2))

def main():
    if STOP.exists(): STOP.unlink()
    child=None; restarts=0
    while not STOP.exists():
        if child is None or child.poll() is not None:
            if child is not None: restarts += 1
            log=open(RUN/"v11.log","ab",buffering=0)
            child=subprocess.Popen([sys.executable,"-u","-m","companyos.autonomous_opportunity_intelligence_v11.server"],
                                   cwd=str(HOME),stdout=log,stderr=subprocess.STDOUT,
                                   stdin=subprocess.DEVNULL,start_new_session=True)
            PID.write_text(str(child.pid)); state("running",child.pid,restarts)
        time.sleep(5)
    if child and child.poll() is None:
        try: child.terminate()
        except Exception: pass
    state("stopped",None,restarts)

if __name__=="__main__":
    main()
