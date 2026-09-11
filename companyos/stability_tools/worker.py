import json,os,signal,time,traceback
from datetime import datetime,timezone
from pathlib import Path

RUNNING=True

def now():
    return datetime.now(timezone.utc).isoformat()

def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True))
    os.replace(tmp,path)

def stop(*_):
    global RUNNING
    RUNNING=False

def run_worker(service_name,engine_factory,interval=300,startup_delay=0):
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    home=Path(os.environ.get("COMPANYOS_HOME",str(Path.home()/"companyos")))
    hb=home/"companyos_runtime"/"service_heartbeats"/(service_name+".json")
    diag=home/"companyos_runtime"/"service_diagnostics"/(service_name+".json")
    for _ in range(startup_delay):
        if not RUNNING:return
        time.sleep(1)
    next_run=0.0;last_error=None;last_status=None
    while RUNNING:
        if time.time()>=next_run:
            try:
                result=engine_factory(home).run()
                last_status=result.get("status") if isinstance(result,dict) else None
                last_error=None
                atomic_json(diag,{"service":service_name,"status":"ok","last_run":now(),"last_error":None})
            except Exception as exc:
                last_error=f"{type(exc).__name__}: {exc}"
                atomic_json(diag,{"service":service_name,"status":"error","last_run":now(),"last_error":last_error,"traceback":traceback.format_exc()[-6000:]})
            next_run=time.time()+max(30,int(interval))
        atomic_json(hb,{"service":service_name,"pid":os.getpid(),"alive":True,"heartbeat_at":now(),"last_error":last_error,"last_result_status":last_status})
        for _ in range(10):
            if not RUNNING:break
            time.sleep(1)
