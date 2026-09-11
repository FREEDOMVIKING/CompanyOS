#!/usr/bin/env python3
import json,sys,time,shutil,hashlib
from pathlib import Path
RT=Path.home()/"companyos"/".companyos_runtime"
BUILDS=RT/"product_builds"; REPORTS=RT/"build_reports"; REL=RT/"releases"; STATE=RT/"release_packager_state.json"
REL.mkdir(parents=True,exist_ok=True)
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d): p.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
def digest(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest()
def package():
    out=[]
    for rp in sorted(REPORTS.glob("*.json")):
        r=load(rp,{})
        if not r.get("build_ok"): continue
        vid=r.get("venture_id"); proj=BUILDS/vid
        if not proj.exists(): continue
        base=REL/f"{vid}-{int(time.time())}"
        arc=shutil.make_archive(str(base),"zip",root_dir=str(proj))
        rec={"venture_id":vid,"archive":arc,"sha256":digest(arc),"release_status":"packaged_internal","ready_for_deployment_handoff":True,"external_deployment_performed":False}
        save(REL/f"{vid}-latest.json",rec); out.append(rec)
    state={"ok":True,"releases_packaged":len(out),"results":out}
    save(STATE,state); return state
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(package() if cmd=="package" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
