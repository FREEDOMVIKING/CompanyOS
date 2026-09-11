from __future__ import annotations
import json, time, hashlib
from pathlib import Path

STAGES=["DISCOVER","VALIDATE","BUILD","TEST","PACKAGE","LAUNCH_READY","LAUNCH","CUSTOMER_ACQUISITION","OPERATE","SCALE"]
ROOT=Path.home()/"companyos"
STATE=ROOT/".companyos_runtime"/"venture_lifecycle_progression.json"

def _load(p,default):
    try:return json.loads(p.read_text())
    except:return default
def _save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True,default=str))

def _files_for(venture):
    key=venture.lower().replace(" ","_")
    roots=[ROOT/"workspace",ROOT/"exports",ROOT/"artifacts",ROOT/"products"]
    out=[]
    for r in roots:
        if not r.exists():continue
        for p in r.rglob("*"):
            if p.is_file() and (key in str(p).lower() or key.replace("_","-") in str(p).lower()):
                out.append(p)
    return out

def infer_stage(venture):
    fs=_files_for(venture); names=" ".join(str(p).lower() for p in fs)
    if any("customer" in str(p).lower() or "lead" in str(p).lower() for p in fs): stage="CUSTOMER_ACQUISITION"
    elif any("export" in str(p).lower() or p.suffix==".zip" for p in fs): stage="LAUNCH_READY"
    elif any("test" in str(p).lower() for p in fs): stage="TEST"
    elif fs: stage="BUILD"
    else: stage="DISCOVER"
    return stage,fs

def fingerprint(fs):
    h=hashlib.sha256()
    for p in sorted(fs,key=lambda x:str(x)):
        try:h.update(str(p).encode());h.update(str(p.stat().st_size).encode());h.update(str(int(p.stat().st_mtime)).encode())
        except:pass
    return h.hexdigest()[:20]

def next_action(stage):
    return {
      "DISCOVER":"validate demand and customer problem before building",
      "VALIDATE":"build the smallest sellable product",
      "BUILD":"test the product against acceptance criteria",
      "TEST":"package a release candidate",
      "PACKAGE":"prepare deployment and launch assets",
      "LAUNCH_READY":"perform launch/deployment steps that are authorized; otherwise prepare an operator-ready launch packet",
      "LAUNCH":"begin measurable customer acquisition",
      "CUSTOMER_ACQUISITION":"measure conversion, fulfill customers, and collect feedback",
      "OPERATE":"improve retention, reliability, margin, and repeatability",
      "SCALE":"expand only from measured evidence"
    }[stage]

def evaluate(venture):
    state=_load(STATE,{"ventures":{}})
    old=state["ventures"].get(venture,{})
    stage,fs=infer_stage(venture); fp=fingerprint(fs)
    repeats=int(old.get("unchanged_cycles",0))+1 if old.get("fingerprint")==fp else 0
    observed_change=old.get("fingerprint") not in (None,fp)
    duplicate_risk=repeats>=3
    rec=old|{"venture":venture,"stage":stage,"next_action":next_action(stage),"fingerprint":fp,
             "unchanged_cycles":repeats,"duplicate_work_risk":duplicate_risk,
             "observed_change":observed_change,"artifact_count":len(fs),"updated_at":time.time()}
    state["ventures"][venture]=rec;_save(STATE,state);return rec

def evaluate_known():
    names=set()
    for r in [ROOT/"workspace",ROOT/"exports"]:
        if r.exists():
            for p in r.iterdir():
                if p.is_dir(): names.add(p.name.replace("-","_"))
    return [evaluate(x) for x in sorted(names)]
