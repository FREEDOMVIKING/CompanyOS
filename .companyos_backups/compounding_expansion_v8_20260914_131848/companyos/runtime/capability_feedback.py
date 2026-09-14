from __future__ import annotations
import ast, hashlib, importlib.util, json, os, time
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
EXP=RT/"capability_expansion"
STATE=RT/"capability_feedback_state.json"
EVENTS=RT/"capability_feedback_events.jsonl"
REGISTRY=ROOT/"companyos/extensions/generated"
STOP=RT/"STOP_CONTINUOUS"

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)

def load(path,default=None):
    if default is None: default={}
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def emit(kind,**kw):
    with EVENTS.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")

def source_fingerprint(path):
    text=path.read_text(encoding="utf-8",errors="replace")
    try:
        tree=ast.parse(text)
        normalized=ast.dump(tree,annotate_fields=False,include_attributes=False)
    except Exception:
        normalized=text
    return hashlib.sha256(normalized.encode()).hexdigest()

def load_capability(path):
    spec=importlib.util.spec_from_file_location("companyos_feedback_"+path.stem,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def benign_context():
    return {"qualification_rejections":[],"profit":{"candidate_count":0,"eligible_count":0},"bridge":{"accepted":0,"rejected":0},"diagnostics":{"findings":[]}}

def cycle():
    old=load(STATE,{})
    prev=old.get("capabilities",{}) if isinstance(old,dict) else {}
    records={}
    REGISTRY.mkdir(parents=True,exist_ok=True)
    exp_state=load(EXP/"state.json",{})
    for path in sorted(REGISTRY.glob("*.py")):
        if path.name.startswith("__"): continue
        cid=path.stem
        rec=dict(prev.get(cid,{}) or {})
        rec.setdefault("successes",0);rec.setdefault("failures",0);rec.setdefault("consecutive_failures",0);rec.setdefault("uses_observed",0)
        rec["capability_id"]=cid
        rec["path"]=str(path.relative_to(ROOT))
        rec["fingerprint"]=source_fingerprint(path)
        rec["checked_at"]=time.time()
        try:
            mod=load_capability(path)
            manifest=mod.capability_manifest()
            result=mod.evaluate(benign_context())
            if not isinstance(manifest,dict): raise TypeError("manifest_not_dict")
            if not isinstance(result,dict): raise TypeError("evaluate_not_dict")
            rec["successes"]+=1;rec["consecutive_failures"]=0;rec["last_error"]=None
            rec["last_manifest"]=manifest
        except Exception as exc:
            rec["failures"]+=1;rec["consecutive_failures"]+=1;rec["last_error"]=repr(exc)
        if exp_state.get("status") in ("capability_promoted_and_used","existing_capability_used") and (exp_state.get("gap") or {}).get("id")==cid:
            rec["uses_observed"]+=1;rec["last_used_at"]=exp_state.get("last_cycle_unix") or time.time()
        total=rec["successes"]+rec["failures"]
        reliability=rec["successes"]/total if total else 0.0
        rec["reliability"]=round(reliability,4)
        if rec["consecutive_failures"]>=3: rec["status"]="quarantined"
        elif rec["successes"]>=3 and reliability>=0.80: rec["status"]="active"
        else: rec["status"]="probation"
        rec["utility_score"]=round(0.75*reliability+0.25*(min(rec["uses_observed"],10)/10.0),4)
        records[cid]=rec
    by_fp={};dups=[]
    for cid,rec in records.items():
        fp=rec.get("fingerprint")
        if not fp: continue
        if fp in by_fp: dups.append({"fingerprint":fp,"capabilities":[by_fp[fp],cid]})
        else: by_fp[fp]=cid
    result={"running":True,"healthy":not any(v.get("status")=="quarantined" for v in records.values()),"last_cycle_unix":time.time(),"capabilities":records,"duplicates":dups,"summary":{"count":len(records),"active":sum(v.get("status")=="active" for v in records.values()),"probation":sum(v.get("status")=="probation" for v in records.values()),"quarantined":sum(v.get("status")=="quarantined" for v in records.values()),"duplicates":len(dups)}}
    atomic(STATE,result);emit("feedback_cycle",summary=result["summary"]);return result

def run():
    delay=max(300,int(os.getenv("COMPANYOS_CAPABILITY_FEEDBACK_INTERVAL_SECONDS","900")))
    while not STOP.exists():
        try:cycle()
        except Exception as exc:atomic(STATE,{"running":True,"healthy":False,"last_cycle_unix":time.time(),"error":repr(exc)})
        time.sleep(delay)

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status"));cmd=a.parse_args().command
    if cmd=="run":run()
    elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
    else:print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
