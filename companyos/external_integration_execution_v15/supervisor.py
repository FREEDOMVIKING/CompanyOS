import subprocess,sys,time,json
from pathlib import Path
from .core import now
HOME=Path.home()/'companyos'; RUN=HOME/'.companyos_enterprise_v15'; RUN.mkdir(parents=True,exist_ok=True); STOP=RUN/'supervisor.stop'; PID=RUN/'runtime.pid'; STATE=RUN/'supervisor_status.json'
def main():
 if STOP.exists(): STOP.unlink()
 child=None; restarts=0
 while not STOP.exists():
  if child is None or child.poll() is not None:
   if child is not None: restarts+=1
   log=open(RUN/'v15.log','ab',buffering=0); child=subprocess.Popen([sys.executable,'-u','-m','companyos.external_integration_execution_v15.server'],cwd=str(HOME),stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True); PID.write_text(str(child.pid)); STATE.write_text(json.dumps({'status':'running','runtime_pid':child.pid,'restart_count':restarts,'updated_at':now()},indent=2))
  time.sleep(5)
if __name__=='__main__': main()
