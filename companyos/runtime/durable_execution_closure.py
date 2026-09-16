from __future__ import annotations
import json, os, time
from pathlib import Path
ROOT=Path.home()/".companyos_runtime"
JOBS=ROOT/"durable_execution_jobs"; STATE=ROOT/"durable_execution_closure_state.json"
EVENTS=ROOT/"durable_execution_closure_events.jsonl"; STOP=ROOT/"STOP_CONTINUOUS"
JOBS.mkdir(parents=True,exist_ok=True)
TERMINAL={"COMPLETED","FAILED","HALTED","BLOCKED","AWAITING_EXTERNAL_GATE"}
def atomic(p,o):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(o,indent=2,sort_keys=True,default=str)+"\n"); t.replace(p)
def load(p,d):
    try:return json.loads(Path(p).read_text())
    except Exception:return d
def emit(kind,**kw):
    with EVENTS.open("a") as f:f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")
def job_path(oid): return JOBS/f"{oid}.json"
def register(*,oid,packet_id,candidate_name,candidate_score,selected_action,fingerprint):
    now=time.time(); p=job_path(oid); old=load(p,{})
    if old:return old
    j={"schema":"companyos.durable_execution.v22","orchestration_id":oid,"action_packet_id":packet_id,
       "candidate_name":candidate_name,"candidate_score":candidate_score,"selected_action":selected_action,
       "fingerprint":fingerprint,"state":"DISPATCHED","created_at":now,"updated_at":now,
       "terminal":False,"cycles":0,"evidence":[],"outcome":None,"last_error":None}
    atomic(p,j); emit("durable_job_registered",orchestration_id=oid,candidate_name=candidate_name); return j
def advance(j):
    oid=j["orchestration_id"]
    try:
        from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
        ceo=AutonomousCEOOrchestrator(); rec=ceo.load(oid)
        if str(rec.state).upper() not in {"COMPLETED","FAILED","HALTED"}:
            ceo.cycle(oid); rec=ceo.load(oid)
        state=str(rec.state or "RUNNING").upper()
        j["state"]=state; j["cycles"]=int(rec.total_cycles or 0); j["active_goal_id"]=rec.active_goal_id
        j["last_decision"]=rec.last_decision; j["outcome"]=rec.final_summary
        j["terminal"]=state in TERMINAL; j["last_error"]=None
    except FileNotFoundError:
        j["state"]="FAILED"; j["terminal"]=True; j["last_error"]="orchestration_record_missing"
    except Exception as e:j["last_error"]=repr(e)
    j["updated_at"]=time.time(); atomic(job_path(oid),j)
    if j["terminal"]:emit("durable_job_terminal",orchestration_id=oid,state=j["state"],outcome=j.get("outcome"))
    return j
def recover_existing():
    recovered=[]
    orch_root=ROOT / "ceo_orchestrations"
    if not orch_root.exists():
        return recovered
    known={p.stem for p in JOBS.glob("*.json")}
    for op in sorted(orch_root.glob("*.json"), key=lambda x:x.stat().st_mtime):
        try:
            x=json.loads(op.read_text())
            oid=str(x.get("orchestration_id") or op.stem)
            if not oid or oid in known:
                continue
            state=str(x.get("state") or "RUNNING").upper()
            j={"schema":"companyos.durable_execution.v23","orchestration_id":oid,
               "action_packet_id":None,"candidate_name":x.get("root_goal") or oid,
               "candidate_score":None,"selected_action":{"action":x.get("root_goal")},
               "fingerprint":"recovered:"+oid,"state":state,
               "created_at":float(x.get("created_at_unix") or op.stat().st_mtime),
               "updated_at":time.time(),"terminal":state in TERMINAL,
               "cycles":int(x.get("total_cycles") or 0),"evidence":[],
               "outcome":x.get("final_summary"),"last_error":None,"recovered":True}
            atomic(job_path(oid),j); recovered.append(oid); known.add(oid)
            emit("durable_job_recovered",orchestration_id=oid,state=state)
        except Exception as e:
            emit("durable_recovery_error",path=str(op),error=repr(e))
    return recovered

def cycle():
    recovered=recover_existing()
    now=time.time(); rows=[]
    for p in JOBS.glob("*.json"):
        j=load(p,{})
        if j and not j.get("terminal"):j=advance(j)
        if j:rows.append(j)
    terminal=[j for j in rows if j.get("terminal")]
    out={"running":True,"healthy":True,"last_cycle_unix":now,"job_count":len(rows),
         "active_count":sum(not j.get("terminal") for j in rows),"terminal_count":len(terminal),
         "completed_count":sum(j.get("state")=="COMPLETED" for j in terminal),
         "failed_count":sum(j.get("state") in {"FAILED","HALTED"} for j in terminal),"recovered_this_cycle":len(recovered)}
    atomic(STATE,out); return out
def run():
    interval=max(10,int(os.getenv("COMPANYOS_DURABLE_EXECUTION_INTERVAL_SECONDS","30")))
    while not STOP.exists():
        try:cycle()
        except Exception as e:atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(e)})
        time.sleep(interval)
if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status"))
    c=a.parse_args().command
    print(json.dumps(cycle() if c=="once" else load(STATE,{"status":"not_run"}),indent=2,sort_keys=True)) if c!="run" else run()
