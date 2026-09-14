from __future__ import annotations
import ast, importlib.util, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve()
RT=ROOT/".companyos_runtime"
BASE=RT/"capability_expansion"
STATE=BASE/"state.json"
EVENTS=BASE/"events.jsonl"
STAGING=BASE/"staging"
PROMOTED=BASE/"promoted"
REGISTRY=ROOT/"companyos/extensions/generated"
TESTS=ROOT/"tests/generated"
STOP=RT/"STOP_CONTINUOUS"

SAFE_IMPORTS={"json","re","math","statistics","time","pathlib","typing","dataclasses","collections","itertools","functools","unittest"}
FORBIDDEN_CALLS={"eval","exec","compile","__import__","open","input","breakpoint"}
FORBIDDEN_TEXT=(
 "openai_api_key","solana_private_key","smtp_password","cloudflare_api_token",
 "seed phrase","private key","disable guard","bypass approval","os.system",
 "subprocess","socket","urllib","requests","http://","https://",
)

def atomic(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 q=p.with_suffix(p.suffix+".tmp")
 q.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
 q.replace(p)

def load(p,default=None):
 if default is None: default={}
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return default

def emit(kind,**kw):
 EVENTS.parent.mkdir(parents=True,exist_ok=True)
 with EVENTS.open("a",encoding="utf-8") as f:
  f.write(json.dumps({"ts":time.time(),"kind":kind,**kw},sort_keys=True,default=str)+"\n")

def diagnostics():
 d=load(RT/"autonomous_diagnostics_state.json")
 findings=((d.get("after") or {}).get("findings") or d.get("findings") or [])
 return {
  "findings":findings,
  "profit":load(RT/"profit_opportunity_status.json"),
  "bridge":load(RT/"candidate_enrichment_bridge_state.json"),
  "services":load(RT/"service_supervisor_state.json").get("services",{}),
 }

def capability_inventory():
 REGISTRY.mkdir(parents=True,exist_ok=True)
 return sorted(p.stem for p in REGISTRY.glob("*.py") if not p.name.startswith("__"))

def derive_gap(ctx):
 for f in ctx["findings"]:
  k=f.get("kind")
  if k=="research_conversion_stall":
   return {"id":"research_quality_analyzer","title":"Research quality analyzer","reason":"Research artifacts are not converting into execution-qualified opportunities."}
  if k=="ssl_hostname_mismatch":
   return {"id":"deployment_route_analyzer","title":"Deployment route analyzer","reason":"Deployment hostname/certificate mismatch is recurring."}
  if k=="import_error":
   return {"id":"import_failure_analyzer","title":"Import failure analyzer","reason":"Import failures are present in diagnostics."}
 p=ctx["profit"]
 if int(p.get("candidate_count") or 0)>0 and int(p.get("eligible_count") or 0)==0:
  return {"id":"candidate_gap_ranker","title":"Candidate qualification gap ranker","reason":"Profit candidates exist but none are execution-qualified."}
 return None

def canonical_paths(capability_id):
 cid=re.sub(r"[^a-zA-Z0-9_]+","_",str(capability_id or "")).strip("_").lower()
 if not cid: raise ValueError("missing capability id")
 return (
  f"companyos/extensions/generated/{cid}.py",
  f"tests/generated/test_{cid}.py",
 )

# COMPANYOS_GENERATION_RECOVERY_V6
def _minimal_generation_prompt(gap,module_path,test_path,attempt):
 return f"""
Return ONE complete JSON object only.
Schema: {{"title":str,"reason":str,"changes":[{{"path":str,"action":str,"content":str,"reason":str}}],"tests":list,"integration":str}}

Build one SAFE ANALYTICAL capability:
id={gap["id"]}
reason={gap["reason"]}

Required files:
- {module_path}
- {test_path}

Module contract:
CAPABILITY_ID = "{gap["id"]}"
def capability_manifest() -> dict
def evaluate(context: dict) -> dict

Rules:
- Pure analysis only.
- No network, shell, subprocess, environment access, file writes, credentials, wallets, finance, approvals, deployment actions, or external sends.
- No markdown.
- No placeholders.
- Keep both files concise.
- Attempt {attempt}.
"""

def _recover_json_object(text):
 text=(text or "").strip()
 if not text:return None
 try:
  obj=json.loads(text)
  return obj if isinstance(obj,dict) else None
 except Exception:
  pass
 # Conservative recovery: locate outermost complete JSON object only.
 start=text.find("{")
 if start < 0:return None
 depth=0; in_string=False; escaped=False
 for i,ch in enumerate(text[start:], start):
  if in_string:
   if escaped:escaped=False
   elif ch=="\\":escaped=True
   elif ch=='"':in_string=False
   continue
  if ch=='"':in_string=True
  elif ch=="{":depth+=1
  elif ch=="}":
   depth-=1
   if depth==0:
    try:
     obj=json.loads(text[start:i+1])
     return obj if isinstance(obj,dict) else None
    except Exception:
     return None
 return None

def model_plan(gap,ctx):
 sys.path.insert(0,str(ROOT/"scripts"))
 from companyos_local_ai_adapter import model_request,extract_json
 module_path,test_path=canonical_paths(gap["id"])
 attempts=[]
 prompts=[
  f"""
Build one NEW SAFE ANALYTICAL CompanyOS capability.

CAPABILITY:
{json.dumps(gap,indent=2)}

CONTEXT:
{json.dumps(ctx,default=str)[:2600]}

Return one complete JSON object in schema title/reason/changes/tests/integration.
Generate exactly TWO Python contents:
1. {module_path}
2. {test_path}

The module must expose CAPABILITY_ID, capability_manifest(), evaluate(context).
Pure analysis only. No network, shell, subprocess, environment access, file writes,
credentials, wallets, finance, approvals, deployment actions, or external sends.
Complete runnable Python only. No markdown. No placeholders.
""",
  _minimal_generation_prompt(gap,module_path,test_path,2),
  _minimal_generation_prompt(gap,module_path,test_path,3),
 ]
 for idx,prompt in enumerate(prompts,1):
  r=model_request(prompt)
  attempts.append({"attempt":idx,"ok":r.get("ok"),"reason":r.get("reason"),"model":r.get("model"),"endpoint":r.get("endpoint")})
  if not r.get("ok"):
   continue
  text=r.get("text","")
  try:
   plan=extract_json(text)
   return {"ok":True,"plan":plan,"model":r.get("model"),"endpoint":r.get("endpoint"),"attempts":attempts,"recovered":False}
  except Exception:
   plan=_recover_json_object(text)
   if isinstance(plan,dict):
    return {"ok":True,"plan":plan,"model":r.get("model"),"endpoint":r.get("endpoint"),"attempts":attempts,"recovered":True}
 return {"ok":False,"reason":"generation_retries_exhausted","attempts":attempts}

# COMPANYOS_TEST_RECOVERY_V5
def _find_test_content(value):
 if isinstance(value,str):
  text=value.strip()
  if ("import unittest" in text or "unittest.TestCase" in text) and len(text) > 40:
   return text
  return None
 if isinstance(value,dict):
  for key in ("content","source","code","test_content","python"):
   found=_find_test_content(value.get(key))
   if found:return found
  for item in value.values():
   found=_find_test_content(item)
   if found:return found
 if isinstance(value,list):
  for item in value:
   found=_find_test_content(item)
   if found:return found
 return None

def _deterministic_contract_test(capability_id):
 cid=re.sub(r"[^a-zA-Z0-9_]+","_",str(capability_id or "")).strip("_").lower()
 lines=[
  "import unittest",
  f"from companyos.extensions.generated.{cid} import CAPABILITY_ID, capability_manifest, evaluate",
  "",
  "class GeneratedCapabilityContractTests(unittest.TestCase):",
  "    def test_manifest_contract(self):",
  f'        self.assertEqual(CAPABILITY_ID, "{cid}")',
  "        manifest = capability_manifest()",
  "        self.assertIsInstance(manifest, dict)",
  "",
  "    def test_evaluate_contract(self):",
  '        result = evaluate({"qualification_rejections":[],"profit":{},"bridge":{}})',
  "        self.assertIsInstance(result, dict)",
  "",
  "    def test_empty_context_is_safe(self):",
  "        result = evaluate({})",
  "        self.assertIsInstance(result, dict)",
  "",
  'if __name__ == "__main__":',
  "    unittest.main()",
 ]
 return "\n".join(lines)+"\n"

def _classify_generated_contents(plan, capability_id=None):
 changes=plan.get("changes") if isinstance(plan,dict) else None
 if not isinstance(changes,list): return None,None,["changes_missing"]
 module_content=None
 test_content=None
 extra=[]
 for ch in changes:
  if not isinstance(ch,dict):
   extra.append("non_dict_change"); continue
  content=ch.get("content")
  if not isinstance(content,str) or not content.strip():
   continue
  path=str(ch.get("path","")).lower()
  looks_test=("test_" in path or path.startswith("tests/") or "import unittest" in content or "unittest.TestCase" in content)
  if looks_test:
   if test_content is None:test_content=content
  else:
   if module_content is None:module_content=content
   else:extra.append("duplicate_module_content")
 if test_content is None:
  test_content=_find_test_content(plan.get("tests"))
 if module_content is None:
  extra.append("module_content_missing")
 if test_content is None and module_content is not None and capability_id:
  test_content=_deterministic_contract_test(capability_id)
 return module_content,test_content,extra

def validate_source(path,content,gap_id,is_test=False):
 errors=[]
 expected=set(canonical_paths(gap_id))
 if path not in expected:errors.append("canonical_path_violation")
 low=content.lower()
 for text in FORBIDDEN_TEXT:
  if text in low:errors.append("forbidden_text:"+text)
 try:tree=ast.parse(content,filename=path)
 except SyntaxError as e:return errors+[f"syntax:{e}"]
 allowed=set(SAFE_IMPORTS)
 for n in ast.walk(tree):
  if isinstance(n,ast.Import):
   mods=[a.name.split(".")[0] for a in n.names]
   for m in mods:
    if m not in allowed and not (is_test and m=="companyos"):errors.append("unsafe_import:"+m)
  elif isinstance(n,ast.ImportFrom):
   m=(n.module or "").split(".")[0]
   if m and m not in allowed and not (is_test and m=="companyos"):errors.append("unsafe_import:"+m)
  elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in FORBIDDEN_CALLS:
   errors.append("forbidden_call:"+n.func.id)
 return sorted(set(errors))

def stage_plan(gap,plan):
 module_path,test_path=canonical_paths(gap["id"])
 module_content,test_content,shape_errors=_classify_generated_contents(plan,gap["id"])
 cid=f"{gap['id']}-{int(time.time())}"
 root=STAGING/cid
 if root.exists():shutil.rmtree(root)
 root.mkdir(parents=True,exist_ok=True)
 errors=list(shape_errors)
 if module_content is not None:errors+=validate_source(module_path,module_content,gap["id"],False)
 if test_content is not None:errors+=validate_source(test_path,test_content,gap["id"],True)
 if not errors:
  a=root/module_path;b=root/test_path
  a.parent.mkdir(parents=True,exist_ok=True);b.parent.mkdir(parents=True,exist_ok=True)
  # COMPANYOS_STAGING_PACKAGE_FIX_V4
  for init_path in (
      root/"companyos/__init__.py",
      root/"companyos/extensions/__init__.py",
      root/"companyos/extensions/generated/__init__.py",
      root/"tests/__init__.py",
      root/"tests/generated/__init__.py",
  ):
   init_path.parent.mkdir(parents=True,exist_ok=True)
   if not init_path.exists():
    init_path.write_text("",encoding="utf-8")
  a.write_text(module_content,encoding="utf-8");b.write_text(test_content,encoding="utf-8")
 atomic(root/"proposal.json",{"gap":gap,"plan":plan,"normalized_paths":[module_path,test_path],"validation_errors":errors})
 return cid,root,sorted(set(errors))

def test_stage(root,gap_id):
 module_path,test_path=canonical_paths(gap_id)
 mod=root/module_path;tst=root/test_path
 env=os.environ.copy();env["PYTHONPATH"]=str(root)+os.pathsep+str(ROOT)
 steps=[]
 cmds=[
  [sys.executable,"-m","py_compile",str(mod),str(tst)],
  [sys.executable,str(tst)],
 ]
 for cmd in cmds:
  cp=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
  steps.append({"cmd":cmd,"returncode":cp.returncode,"stdout":cp.stdout[-4000:],"stderr":cp.stderr[-4000:]})
  if cp.returncode!=0:return False,steps
 return True,steps

def promote(root,gap_id,cid):
 module_path,test_path=canonical_paths(gap_id)
 src=root/module_path;tst=root/test_path
 dst=ROOT/module_path;tdst=ROOT/test_path
 dst.parent.mkdir(parents=True,exist_ok=True);tdst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(src,dst);shutil.copy2(tst,tdst)
 receipt={"candidate_id":cid,"capability_id":gap_id,"module":module_path,"test":test_path,"promoted_at":time.time()}
 PROMOTED.mkdir(parents=True,exist_ok=True);atomic(PROMOTED/f"{cid}.json",receipt)
 return receipt

def rollback(gap_id):
 module_path,test_path=canonical_paths(gap_id)
 (ROOT/module_path).unlink(missing_ok=True);(ROOT/test_path).unlink(missing_ok=True)

def run_capability(gap_id,context):
 module_path,_=canonical_paths(gap_id);p=ROOT/module_path
 spec=importlib.util.spec_from_file_location("companyos_generated_"+gap_id,p)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return {"manifest":m.capability_manifest(),"result":m.evaluate(context)}

def cycle():
 ctx=diagnostics();inv=capability_inventory();gap=derive_gap(ctx)
 st={"running":True,"last_cycle_unix":time.time(),"inventory":inv,"gap":gap}
 if not gap:
  st.update(status="no_gap_detected",healthy=True);atomic(STATE,st);return st
 if gap["id"] in inv:
  try:st["execution"]=run_capability(gap["id"],ctx);st.update(status="existing_capability_used",healthy=True)
  except Exception as e:st.update(status="existing_capability_failed",healthy=False,error=repr(e))
  atomic(STATE,st);return st
 gen=model_plan(gap,ctx);st["generation"]=gen
 if not gen.get("ok"):
  st.update(status="generation_failed",healthy=False);atomic(STATE,st);return st
 cid,root,errors=stage_plan(gap,gen["plan"]);st["candidate_id"]=cid;st["validation_errors"]=errors
 if errors:
  st.update(status="candidate_rejected_validation",healthy=True);atomic(STATE,st);emit("CANDIDATE_REJECTED",capability=gap["id"],errors=errors);return st
 ok,tests=test_stage(root,gap["id"]);st["tests"]=tests
 if not ok:
  st.update(status="candidate_rejected_tests",healthy=True);atomic(STATE,st);emit("CANDIDATE_REJECTED_TESTS",capability=gap["id"]);return st
 st["promotion"]=promote(root,gap["id"],cid)
 try:
  st["execution"]=run_capability(gap["id"],ctx)
  st.update(status="capability_promoted_and_used",healthy=True)
 except Exception as e:
  rollback(gap["id"]);st.update(status="canary_failed_rolled_back",healthy=False,error=repr(e))
 atomic(STATE,st);emit("CAPABILITY_CYCLE",capability=gap["id"],status=st["status"]);return st

def run():
 delay=max(300,int(os.getenv("COMPANYOS_CAPABILITY_EXPANSION_INTERVAL_SECONDS","1800")))
 while not STOP.exists():
  try:cycle()
  except Exception as e:atomic(STATE,{"running":True,"healthy":False,"status":"cycle_exception","error":repr(e),"last_cycle_unix":time.time()})
  time.sleep(delay)

if __name__=="__main__":
 import argparse
 a=argparse.ArgumentParser();a.add_argument("command",nargs="?",default="run",choices=("run","once","status","inventory"));cmd=a.parse_args().command
 if cmd=="run":run()
 elif cmd=="once":print(json.dumps(cycle(),indent=2,sort_keys=True,default=str))
 elif cmd=="status":print(json.dumps(load(STATE,{"status":"not_run"}),indent=2,sort_keys=True,default=str))
 else:print(json.dumps({"capabilities":capability_inventory()},indent=2))
