from __future__ import annotations
import ast,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"
BASE=RT/"capability_expansion"; STATE=BASE/"state.json"; EVENTS=BASE/"events.jsonl"
STAGING=BASE/"staging"; PROMOTED=BASE/"promoted"; REGISTRY=ROOT/"companyos/extensions/generated"; TESTS=ROOT/"tests/generated"; STOP=RT/"STOP_CONTINUOUS"
SAFE_IMPORTS={"json","re","math","statistics","time","pathlib","typing","dataclasses","collections","itertools","functools"}
FORBIDDEN_NAMES={"eval","exec","compile","__import__","open","input","breakpoint"}
FORBIDDEN_TEXT=("OPENAI_API_KEY","SOLANA_PRIVATE_KEY","SMTP_PASSWORD","CLOUDFLARE_API_TOKEN","wallet","private key","seed phrase","approval gate","disable guard","bypass","subprocess","os.system","socket","urllib","requests","http://","https://")
def atomic(p,o):
 p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp"); q.write_text(json.dumps(o,indent=2,sort_keys=True,default=str)+"\n"); q.replace(p)
def load(p,d=None):
 try:return json.loads(p.read_text())
 except:return {} if d is None else d
def emit(k,**kw):
 EVENTS.parent.mkdir(parents=True,exist_ok=True)
 with EVENTS.open("a") as f:f.write(json.dumps({"ts":time.time(),"kind":k,**kw},sort_keys=True,default=str)+"\n")
def context():
 d=load(RT/"autonomous_diagnostics_state.json"); findings=((d.get("after") or {}).get("findings") or d.get("findings") or [])
 return {"findings":findings,"profit":load(RT/"profit_opportunity_status.json"),"bridge":load(RT/"candidate_enrichment_bridge_state.json"),"services":load(RT/"service_supervisor_state.json").get("services",{})}
def inventory():
 REGISTRY.mkdir(parents=True,exist_ok=True); return [p.stem for p in sorted(REGISTRY.glob("*.py")) if not p.name.startswith("__")]
def derive_gap(c):
 for f in c["findings"]:
  k=f.get("kind")
  if k=="research_conversion_stall":return {"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"Research is not converting into execution-qualified opportunities.","success":"Rank exact enrichment gaps and recommend concrete field-level fixes."}
  if k=="ssl_hostname_mismatch":return {"id":"deployment_route_analyzer","title":"Deployment route analyzer","reason":"Deployment hostname/certificate failures recur.","success":"Classify route risk and recommend safe rediscovery checks."}
  if k=="import_error":return {"id":"import_failure_analyzer","title":"Import failure analyzer","reason":"Import errors were detected.","success":"Classify likely causes and safe verification steps."}
 p=c["profit"]
 if p.get("candidate_count",0)>0 and p.get("eligible_count",0)==0:return {"id":"candidate_gap_ranker","title":"Candidate gap ranker","reason":"Candidates exist but none qualify for execution.","success":"Rank missing evidence/economics/action fields by qualification impact."}
 return None
def model_plan(g,c):
 sys.path.insert(0,str(ROOT/"scripts")); from companyos_local_ai_adapter import model_request,extract_json
 prompt=f'''Build one NEW SAFE ANALYTICAL capability for CompanyOS.\nGAP:\n{json.dumps(g,indent=2)}\nCONTEXT:\n{json.dumps(c,default=str)[:4500]}\nRules: create exactly companyos/extensions/generated/{g['id']}.py and tests/generated/test_{g['id']}.py. Module must expose CAPABILITY_ID, capability_manifest()->dict, evaluate(context:dict)->dict. Pure analysis only: no network, subprocess, shell, environment, filesystem writes, credentials, wallets, finance, approvals, deployments, or external sends. Allowed imports only: {sorted(SAFE_IMPORTS)}. Tests must verify manifest and at least two evaluate behaviors. Complete code only.'''
 r=model_request(prompt)
 if not r.get("ok"):return {"ok":False,"reason":r.get("reason")}
 try:return {"ok":True,"plan":extract_json(r.get("text","")),"model":r.get("model")}
 except Exception as e:return {"ok":False,"reason":f"parse_failed:{e}"}
def validate(path,content,gid):
 allowed={f"companyos/extensions/generated/{gid}.py",f"tests/generated/test_{gid}.py"}; errs=[]
 if path not in allowed:return ["path_not_allowed"]
 low=content.lower()
 for x in FORBIDDEN_TEXT:
  if x.lower() in low:errs.append("forbidden:"+x)
 try:t=ast.parse(content,filename=path)
 except SyntaxError as e:return [f"syntax:{e}"]
 for n in ast.walk(t):
  if isinstance(n,(ast.Import,ast.ImportFrom)):
   mods=[a.name.split('.')[0] for a in n.names] if isinstance(n,ast.Import) else [(n.module or '').split('.')[0]]
   for m in mods:
    if m and m not in SAFE_IMPORTS and not m.startswith("companyos"):errs.append("unsafe_import:"+m)
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in FORBIDDEN_NAMES:errs.append("forbidden_call:"+n.func.id)
 return sorted(set(errs))
def stage(g,plan):
 cid=f"{g['id']}-{int(time.time())}"; root=STAGING/cid; shutil.rmtree(root,ignore_errors=True); root.mkdir(parents=True)
 expected={f"companyos/extensions/generated/{g['id']}.py",f"tests/generated/test_{g['id']}.py"}; got=set(); errs=[]
 for ch in plan.get("changes") or []:
  if not isinstance(ch,dict):errs.append("non_dict_change");continue
  path=str(ch.get("path","")); content=str(ch.get("content","")); got.add(path); errs+=validate(path,content,g['id'])
  if path in expected:
   d=root/path; d.parent.mkdir(parents=True,exist_ok=True); d.write_text(content)
 if got!=expected:errs.append("exact_two_paths_required")
 atomic(root/"proposal.json",{"gap":g,"plan":plan,"validation_errors":errs}); return cid,root,errs
def run_tests(root,gid):
 env=os.environ.copy(); env["PYTHONPATH"]=str(root)+os.pathsep+str(ROOT); steps=[]
 for cmd in ([sys.executable,"-m","py_compile",str(root/f"companyos/extensions/generated/{gid}.py"),str(root/f"tests/generated/test_{gid}.py")],[sys.executable,"-m","unittest",str(root/f"tests/generated/test_{gid}.py"),"-v"]):
  cp=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=60); steps.append({"returncode":cp.returncode,"stdout":cp.stdout[-3000:],"stderr":cp.stderr[-3000:]})
  if cp.returncode!=0:return False,steps
 return True,steps
def promote(root,gid,cid):
 REGISTRY.mkdir(parents=True,exist_ok=True); TESTS.mkdir(parents=True,exist_ok=True)
 dst=REGISTRY/f"{gid}.py"; tdst=TESTS/f"test_{gid}.py"; shutil.copy2(root/f"companyos/extensions/generated/{gid}.py",dst); shutil.copy2(root/f"tests/generated/test_{gid}.py",tdst)
 r={"candidate_id":cid,"capability_id":gid,"promoted_at":time.time(),"module":str(dst.relative_to(ROOT))}; PROMOTED.mkdir(parents=True,exist_ok=True); atomic(PROMOTED/f"{cid}.json",r); return r
def use(gid,c):
 import importlib.util
 p=REGISTRY/f"{gid}.py"; spec=importlib.util.spec_from_file_location("generated_"+gid,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return {"manifest":m.capability_manifest(),"result":m.evaluate(c)}
def cycle():
 c=context(); inv=inventory(); g=derive_gap(c); s={"running":True,"last_cycle_unix":time.time(),"inventory":inv,"gap":g}
 if not g:s["status"]="no_gap_detected";s["healthy"]=True;atomic(STATE,s);return s
 if g["id"] in inv:
  try:s["execution"]=use(g["id"],c);s["status"]="existing_capability_used";s["healthy"]=True
  except Exception as e:s["status"]="existing_capability_failed";s["error"]=repr(e);s["healthy"]=False
  atomic(STATE,s);emit("CAPABILITY_USED",capability=g["id"],status=s["status"]);return s
 gen=model_plan(g,c);s["generation"]=gen
 if not gen.get("ok"):s["status"]="generation_failed";s["healthy"]=False;atomic(STATE,s);return s
 cid,root,errs=stage(g,gen["plan"]);s["candidate_id"]=cid;s["validation_errors"]=errs
 if errs:s["status"]="candidate_rejected_validation";s["healthy"]=True;atomic(STATE,s);return s
 ok,steps=run_tests(root,g["id"]);s["tests"]=steps
 if not ok:s["status"]="candidate_rejected_tests";s["healthy"]=True;atomic(STATE,s);return s
 s["promotion"]=promote(root,g["id"],cid)
 try:s["execution"]=use(g["id"],c);s["status"]="capability_promoted_and_used";s["healthy"]=True
 except Exception as e:
  (REGISTRY/f"{g['id']}.py").unlink(missing_ok=True);(TESTS/f"test_{g['id']}.py").unlink(missing_ok=True);s["status"]="canary_failed_rolled_back";s["error"]=repr(e);s["healthy"]=False
 atomic(STATE,s);emit("CAPABILITY_CYCLE",capability=g["id"],status=s["status"]);return s
def run():
 delay=max(300,int(os.getenv("COMPANYOS_CAPABILITY_EXPANSION_INTERVAL_SECONDS","1800")))
 while not STOP.exists():
  try:cycle()
  except Exception as e:atomic(STATE,{"running":True,"healthy":False,"status":"cycle_exception","error":repr(e),"last_cycle_unix":time.time()})
  time.sleep(delay)
if __name__=="__main__":
 import argparse
 a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status","inventory"));q=a.parse_args().command
 if q=="run":run()
 elif q=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
 elif q=="status":print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
 else:print(json.dumps({"capabilities":inventory()},indent=2))
