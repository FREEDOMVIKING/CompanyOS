from __future__ import annotations
import hashlib,json,os,time
from pathlib import Path
ROOT=Path.home()/"companyos"; RT=ROOT/".companyos_runtime"
QUEUE=RT/"profit_execution_action_queue.json"; STATE=RT/"profit_to_action_closure_state.json"
EVENTS=RT/"profit_to_action_closure_events.jsonl"; STOP=RT/"STOP_CONTINUOUS"

def load(p,d):
    try:return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:return d
def atomic(p,o):
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(o,indent=2,sort_keys=True,default=str)+"\\n",encoding="utf-8"); t.replace(p)
def emit(k,**kw):
    with EVENTS.open("a",encoding="utf-8") as f:f.write(json.dumps({"ts":time.time(),"kind":k,**kw},sort_keys=True,default=str)+"\\n")
def priority(p):
    c=p.get("decision_closure") if isinstance(p.get("decision_closure"),dict) else {}
    r={"promote_to_guarded_execution":3,"continue_research":2,None:1,"deprioritize":0}.get(c.get("decision"),1)
    return (r,float(p.get("candidate_score") or 0),float(p.get("created_at") or 0))
def packets():
    q=load(QUEUE,{"actions":[]}); rows=q.get("actions",[]) if isinstance(q,dict) else []; out=[]
    for p in rows:
        if not isinstance(p,dict) or not p.get("recommended_actions"):continue
        c=p.get("decision_closure") if isinstance(p.get("decision_closure"),dict) else {}
        if c.get("decision")=="deprioritize":continue
        out.append(p)
    return sorted(out,key=priority,reverse=True)
def choose(p):
    a=[x for x in p.get("recommended_actions",[]) if isinstance(x,dict) and str(x.get("action") or "").strip()]
    a.sort(key=lambda x:float(x.get("confidence") or 0),reverse=True); return a[0] if a else None
def fingerprint(p,a):
    return hashlib.sha256((str(p.get("action_packet_id") or "")+"|"+str(a.get("action") or "")).encode()).hexdigest()[:24]
def goal(p,a):
    safe={"action_packet_id":p.get("action_packet_id"),"candidate_name":p.get("candidate_name"),
          "candidate_score":p.get("candidate_score"),"selected_action":a,"decision_closure":p.get("decision_closure")}
    return """PROFIT-TO-ACTION CLOSURE - GUARDED EXECUTION
Advance the selected CompanyOS opportunity by completing the concrete action below.

EXECUTION CONTRACT:
- This is execution-oriented CEO work, not status-only analysis.
- Start with the selected action and create concrete internal work immediately.
- Prefer the smallest reversible measurable step that can change the opportunity decision.
- Persist evidence, outputs, pass/fail criteria, and resulting candidate-state changes.
- Never fabricate customers, demand, evidence, revenue, pricing, costs, profit, or probability.
- Outreach, publication, deployment, purchases, legal commitments, credential use, signing,
  financial transactions, destructive actions, and irreversible/external actions MUST pass
  existing CompanyOS connector, approval, finance, signer, deployment, legal, and safety gates.
- A blocked action is not permission to bypass a gate. Record the blocker and perform the next
  permitted reversible validation step.
- Feed measurable results back into qualification and profit scoring.

CURRENT EXECUTION PACKET:
"""+json.dumps(safe,indent=2,default=str)
def cycle():
    now=time.time(); st=load(STATE,{"processed":{},"dispatches":[]}); done=st.get("processed",{})
    if not isinstance(done,dict):done={}
    cooldown=max(120,int(os.getenv("COMPANYOS_PROFIT_ACTION_COOLDOWN_SECONDS","600")))
    rows=packets(); selected=None
    for p in rows:
        a=choose(p)
        if not a:continue
        fid=fingerprint(p,a)
        if now-float(done.get(fid,0) or 0)>=cooldown:selected=(p,a,fid);break
    if not selected:
        out={**st,"running":True,"healthy":True,"last_cycle_unix":now,"status":"no_new_executable_packet","eligible_packet_count":len(rows)}
        atomic(STATE,out);return out
    p,a,fid=selected
    from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
    rec=AutonomousCEOOrchestrator().start(goal=goal(p,a),max_cycles=80,max_follow_up_depth=4,priority_base=260)
    oid=getattr(rec,"orchestration_id",None); done[fid]=now
    d={"ts":now,"fingerprint":fid,"action_packet_id":p.get("action_packet_id"),"candidate_name":p.get("candidate_name"),
       "candidate_score":p.get("candidate_score"),"selected_action":a,"orchestration_id":oid}
    arr=st.get("dispatches",[]); arr=arr if isinstance(arr,list) else []; arr.append(d)
    out={"running":True,"healthy":True,"last_cycle_unix":now,"status":"guarded_action_dispatched",
         "processed":done,"dispatches":arr[-100:],"last_dispatch":d,"eligible_packet_count":len(rows)}
    atomic(STATE,out);emit("guarded_action_dispatched",**d);return out
def run():
    interval=max(120,int(os.getenv("COMPANYOS_PROFIT_ACTION_INTERVAL_SECONDS","300")))
    while not STOP.exists():
        try:cycle()
        except Exception as e:
            atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"status":"cycle_error","error":repr(e)})
            emit("cycle_error",error=repr(e))
        time.sleep(interval)
if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status"))
    c=a.parse_args().command
    if c=="run":run()
    elif c=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
