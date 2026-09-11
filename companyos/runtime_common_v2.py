import json,os,tempfile,signal,time
from datetime import datetime,timezone
from pathlib import Path
def now(): return datetime.now(timezone.utc).isoformat()
def read_json(path,default):
    try:return json.loads(Path(path).read_text())
    except Exception:return default
def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix=path.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def run_forever(name,factory,interval=300):
    running=True
    def stop(*_):
        nonlocal running;running=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    home=Path.home()/"companyos"
    while running:
        try:
            r=factory(home).run();print(json.dumps({"service":name,"status":r.get("status"),"at":now()}),flush=True)
        except Exception as e:
            print(json.dumps({"service":name,"error":str(e),"at":now()}),flush=True)
        for _ in range(interval):
            if not running:break
            time.sleep(1)
