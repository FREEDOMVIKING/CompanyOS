from __future__ import annotations
import json,os,re,subprocess,time
from pathlib import Path
ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"
STATE=RT/"autonomous_diagnostics_state.json"; EVENTS=RT/"autonomous_diagnostics_events.jsonl"; STOP=RT/"STOP_CONTINUOUS"
PATS={"ssl_hostname_mismatch":r"CERTIFICATE_VERIFY_FAILED|Hostname mismatch|certificate is not valid","connection_refused":r"Connection refused","http_404":r"HTTP Error 404|404 Not Found","permission_denied":r"Permission denied","syntax_error":r"SyntaxError|IndentationError|TabError","import_error":r"ModuleNotFoundError|ImportError","disk_full":r"No space left on device"}
def atomic(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp"); q.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+"\\n"); q.replace(p)
def load(p):
 try:return json.loads(p.read_text())
 except:return {}
def diagnose():
 sup=load(RT/"service_supervisor_state.json"); findings=[]
 for n,r in (sup.get("services") or {}).items():
  if not r.get("running"):findings.append({"kind":"service_health","severity":"high","detail":{"service":n,"problem":"not_running"}})
  if int(r.get("consecutive_failures") or 0)>0:findings.append({"kind":"service_health","severity":"high","detail":{"service":n,"problem":"consecutive_failures"}})
 for p in RT.glob("*.log"):
  try:t=p.read_text(errors="replace")[-120000:]
  except:continue
  for k,rx in PATS.items():
   h=len(re.findall(rx,t,re.I))
   if h:findings.append({"kind":k,"severity":"high" if k in ("disk_full","syntax_error","import_error") else "medium","source":str(p.relative_to(ROOT)),"hits":h})
 b=load(RT/"candidate_enrichment_bridge_state.json")
 if int(b.get("scanned") or 0)>0 and int(b.get("accepted") or 0)==0:findings.append({"kind":"research_conversion_stall","severity":"medium","detail":{"scanned":b.get("scanned"),"rejected":b.get("rejected")}})
 return {"ts":time.time(),"supervisor_running":bool(sup.get("running")),"findings":findings}
def plan(r):
 out=[]
 for f in r["findings"]:
  if f["kind"]=="service_health":out.append({"repair":"supervisor_restart","reason":f["detail"]})
  elif f["kind"]=="research_conversion_stall":out.append({"repair":"request_targeted_enrichment","reason":f["detail"]})
  elif f["kind"]=="ssl_hostname_mismatch":out.append({"repair":"quarantine_stale_deployment_route","reason":f.get("source")})
 return out
def apply(a):
 res=[]; kinds={x["repair"] for x in a}
 if "request_targeted_enrichment" in kinds:
  atomic(RT/"diagnostics_targeted_enrichment_requested.json",{"requested_at":time.time(),"instruction":"Prioritize enrichment queue; do not broaden generic research."});res.append({"repair":"request_targeted_enrichment","ok":True})
 if "quarantine_stale_deployment_route" in kinds:
  atomic(RT/"diagnostics_deployment_route_quarantine.json",{"created_at":time.time(),"policy":"Do not retry identical failing hostname. Require rediscovery/revalidation."});res.append({"repair":"quarantine_stale_deployment_route","ok":True})
 if "supervisor_restart" in kinds:
  c=ROOT/"scripts/companyosctl"
  if c.exists():
   p=subprocess.run([str(c),"restart"],cwd=ROOT,text=True,capture_output=True,timeout=45);res.append({"repair":"supervisor_restart","ok":p.returncode==0})
 return res
def cycle():
 before=diagnose(); repairs=apply(plan(before)); after=diagnose()
 x={"running":True,"healthy":not any(f["severity"]=="high" for f in after["findings"]),"last_cycle_unix":time.time(),"before":before,"repairs":repairs,"after":after};atomic(STATE,x)
 with EVENTS.open("a") as f:f.write(json.dumps({"ts":time.time(),"event":"diagnostic_cycle","healthy":x["healthy"],"repairs":repairs})+"\\n")
 return x
def run():
 delay=max(60,int(os.getenv("COMPANYOS_DIAGNOSTICS_INTERVAL_SECONDS","300")))
 while not STOP.exists():
  try:cycle()
  except Exception as e:atomic(STATE,{"running":True,"healthy":False,"error":repr(e),"last_cycle_unix":time.time()})
  time.sleep(delay)
if __name__=="__main__":
 import sys
 print(json.dumps(cycle(),indent=2,default=str)) if "--once" in sys.argv else run()
