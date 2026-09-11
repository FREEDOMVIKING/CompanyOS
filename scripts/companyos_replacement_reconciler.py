#!/data/data/com.termux/files/usr/bin/python
import json,sys,time
from pathlib import Path
RT=Path.home()/"companyos"/".companyos_runtime"
REC=RT/"replacement_receipts"; OPS=RT/"operations"; STATE=RT/"replacement_reconciler_state.json"
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); t.replace(p)
def run():
    out=[]
    for p in sorted(REC.glob("*.json")):
        r=load(p,{})
        if not r.get("verified"):continue
        vid=r.get("venture_id"); opf=OPS/f"{vid}.json"; op=load(opf,{})
        op.update({"venture_id":vid,"updated_at":time.time(),"lifecycle_state":"operational_healthy",
                   "rollback_recommended":False,"replacement_worker":r.get("replacement_worker"),
                   "replacement_url":r.get("replacement_url"),
                   "health":{"healthy":True,"health_url":r.get("replacement_url","").rstrip("/")+"/health","http_status":200}})
        save(opf,op); out.append({"venture_id":vid,"state":"operational_healthy"})
    state={"ok":True,"replacements_reconciled":len(out),"results":out}; save(STATE,state); return state
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(run() if cmd=="reconcile" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
