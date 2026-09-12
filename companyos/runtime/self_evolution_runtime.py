import fcntl,json,os,time
from pathlib import Path
from .self_evolution_engine import EV,cycle
STATE=EV/"runtime_state.json"; LOCK=EV/"runtime.lock"
def save(d):
    t=STATE.with_suffix(".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); t.replace(STATE)
def main():
    interval=max(300,int(os.getenv("COMPANYOS_SELF_EVOLUTION_INTERVAL_SECONDS","1800"))); delay=max(20,int(os.getenv("COMPANYOS_SELF_EVOLUTION_INITIAL_DELAY_SECONDS","60")))
    f=LOCK.open("a+")
    try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return 2
    save({"running":True,"pid":os.getpid(),"interval_seconds":interval,"started_at":time.time(),"next_cycle_at":time.time()+delay}); time.sleep(delay)
    while True:
        st=time.time()
        try:r=cycle(); row={"running":True,"pid":os.getpid(),"interval_seconds":interval,"last_cycle_started":st,"last_cycle_finished":time.time(),"last_ok":r.get("ok"),"last_status":r.get("status"),"next_cycle_at":time.time()+interval}
        except Exception as e:row={"running":True,"pid":os.getpid(),"interval_seconds":interval,"last_ok":False,"last_status":"exception","error":str(e),"next_cycle_at":time.time()+interval}
        save(row); time.sleep(interval)
if __name__=="__main__":raise SystemExit(main())
