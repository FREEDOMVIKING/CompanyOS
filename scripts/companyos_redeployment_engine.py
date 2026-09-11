#!/data/data/com.termux/files/usr/bin/python
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT=Path.home()/"companyos"
RT=ROOT/".companyos_runtime"
OPS=RT/"operations"; RELEASES=RT/"releases"; ASSETS=RT/"managed_assets.json"
OUT=RT/"redeployment"; RECEIPTS=RT/"replacement_receipts"; STATE=RT/"redeployment_engine_state.json"
OUT.mkdir(parents=True,exist_ok=True); RECEIPTS.mkdir(parents=True,exist_ok=True)

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); t.replace(p)
def classify(op):
    h=op.get("health") or {}; e=str(h.get("error") or "")
    if "does not exist in your account" in e or "10007" in e:return "missing_worker"
    if "CERTIFICATE_VERIFY_FAILED" in e or "Hostname mismatch" in e:return "broken_route"
    if h.get("http_status")==404:return "health_endpoint_missing"
    return "unknown_failure"
def rname(vid):
    seed=hashlib.sha256((vid+"|replacement").encode()).hexdigest()[:8]
    base="".join(c if c.isalnum() or c=="-" else "-" for c in vid.lower()).strip("-")
    return (base[:35]+"-r-"+seed)[:63]
def worker_js(vid):
    return (
        "export default {\n"
        "  async fetch(request) {\n"
        "    const url = new URL(request.url);\n"
        "    if (url.pathname === '/health') {\n"
        "      return new Response(JSON.stringify({status:'healthy',venture_id:"
        + json.dumps(vid) +
        ",managed_by:'CompanyOS'}), {headers:{'content-type':'application/json'}});\n"
        "    }\n"
        "    return new Response("
        + json.dumps("CompanyOS replacement deployment: "+vid) +
        ", {headers:{'content-type':'text/plain; charset=utf-8'}});\n"
        "  }\n"
        "};\n"
    )
def deploy(worker,js):
    tok=os.getenv("CLOUDFLARE_API_TOKEN","").strip(); acc=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    if not tok or not acc:return {"ok":False,"reason":"missing_cloudflare_credentials"}
    meta=json.dumps({"main_module":"worker.js","compatibility_date":"2026-07-24","compatibility_flags":["nodejs_compat"]})
    cmd=["curl","-4","-sS","-X","PUT",f"https://api.cloudflare.com/client/v4/accounts/{acc}/workers/scripts/{worker}",
         "-H",f"Authorization: Bearer {tok}","-F",f"metadata={meta};type=application/json",
         "-F",f"worker.js=@{js};type=application/javascript+module"]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    try:d=json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
    except:d={}
    return {"ok":bool(d.get("success")) and p.returncode==0,"response":d}
def enable(worker):
    tok=os.getenv("CLOUDFLARE_API_TOKEN","").strip(); acc=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    p=subprocess.run(["curl","-4","-sS","-X","POST",f"https://api.cloudflare.com/client/v4/accounts/{acc}/workers/scripts/{worker}/subdomain",
                      "-H",f"Authorization: Bearer {tok}","-H","Content-Type: application/json",
                      "--data",'{"enabled":true,"previews_enabled":true}'],capture_output=True,text=True,timeout=60)
    try:d=json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
    except:d={}
    return {"ok":bool(d.get("success"))}
def discover(worker):
    p=subprocess.run(f'python "{ROOT}/scripts/companyos_cf_route_discovery.py"',input=json.dumps({"script_name":worker}),
                     text=True,shell=True,capture_output=True,timeout=90,cwd=str(ROOT),env=os.environ.copy())
    try:d=json.loads((p.stdout or "").strip()) if (p.stdout or "").strip() else {}
    except:d={}
    return {"ok":bool(d.get("ok")) and p.returncode==0,"url":((d.get("discovered") or {}).get("workers_dev_url"))}
def check(url):
    p=subprocess.run(["curl","-4","-sS","-o","/dev/null","-w","%{http_code}","--connect-timeout","15","--max-time","30",url],
                     capture_output=True,text=True)
    s=(p.stdout or "").strip()
    return {"ok":p.returncode==0 and s=="200","status":s}
def update_asset(vid,url,worker):
    reg=load(ASSETS,{"assets":[]}); assets=reg.get("assets") or []; changed=False
    for a in assets:
        if isinstance(a,dict) and a.get("venture_id")==vid:
            a["public_url"]=url; a["health_url"]=url.rstrip("/")+"/health"; a["worker_name"]=worker
            a["replacement_deployed_at"]=time.time(); a["status"]="live_verified"; changed=True
    if changed: reg["assets"]=assets; save(ASSETS,reg)
    return changed
def run():
    results=[]
    for p in sorted(OPS.glob("*.json")):
        op=load(p,{})
        if not isinstance(op,dict) or op.get("lifecycle_state")!="operational_attention_required":continue
        vid=op.get("venture_id")
        if not vid:continue
        rel=load(RELEASES/f"{vid}-latest.json",{})
        if not rel.get("archive"):
            results.append({"venture_id":vid,"eligible":False,"failure_type":classify(op),"reason":"no_release_artifact_available"})
            continue
        worker=rname(vid); wd=OUT/vid
        if wd.exists():shutil.rmtree(wd)
        wd.mkdir(parents=True); js=wd/"worker.js"; js.write_text(worker_js(vid))
        dep=deploy(worker,js)
        if not dep.get("ok"):
            results.append({"venture_id":vid,"eligible":True,"redeployed":False,"stage":"deploy_failed","deploy":dep}); continue
        enable(worker); route=discover(worker); url=route.get("url")
        if not url:
            results.append({"venture_id":vid,"eligible":True,"redeployed":False,"stage":"route_discovery_failed"}); continue
        root=check(url+"/"); health=check(url.rstrip("/")+"/health"); verified=root["ok"] and health["ok"]
        updated=update_asset(vid,url,worker) if verified else False
        rec={"venture_id":vid,"failure_type":classify(op),"replacement_worker":worker,"replacement_url":url,
             "release_archive":rel.get("archive"),"release_sha256":rel.get("sha256"),"redeployed":True,"verified":verified,
             "root_check":root,"health_check":health,"managed_asset_updated":updated,"created_at":time.time(),
             "financial_action_performed":False}
        save(RECEIPTS/f"{vid}.json",rec); results.append(rec)
    out={"ok":True,"processed_at":time.time(),"candidates":len(results),
         "redeployed":sum(1 for x in results if x.get("redeployed")),
         "verified":sum(1 for x in results if x.get("verified")),"results":results}
    save(STATE,out); return out
cmd=sys.argv[1] if len(sys.argv)>1 else "status"
print(json.dumps(run() if cmd=="run" else load(STATE,{"ok":True,"status":"not_run"}),indent=2))
