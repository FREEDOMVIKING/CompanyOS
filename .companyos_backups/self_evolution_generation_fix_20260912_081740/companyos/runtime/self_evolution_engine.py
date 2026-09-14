from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"; EV=RT/"self_evolution"
WT=EV/"worktrees"; RC=EV/"receipts"; BK=EV/"promotion_backups"; STATE=EV/"state.json"; LEDGER=EV/"ledger.jsonl"
for p in (EV,WT,RC,BK): p.mkdir(parents=True,exist_ok=True)

SAFE_PREFIXES=("companyos/","companyos_modules/","scripts/","tests/","templates/")
EXACT_PROTECTED={
 "companyos/runtime/self_evolution_engine.py","companyos/runtime/self_evolution_runtime.py",
 "companyos/runtime/service_supervisor.py","companyos/runtime/runtime_control.py",
 "scripts/companyos_evolutionctl","scripts/companyos_adaptive_self_build.py",
}
PROTECTED_WORDS=("wallet","finance","banking","payment","credential","secret","security","auth","approval","governance","guardrail","policy_gate","deployment_gate","connector","solana","private_key")
PROTECTED_TERMS=("OPENAI_API_KEY","CLOUDFLARE_API_TOKEN","SOLANA_PRIVATE_KEY","SMTP_PASSWORD","SEED_PHRASE","MNEMONIC","COMPANYOS_DAILY_FINANCE_CAP_USD","COMPANYOS_SINGLE_FINANCE_CAP_USD","COMPANYOS_ENABLE_LIVE_FINANCE")
FORBIDDEN=("rm -rf","chmod 777","curl | sh","wget | sh","disable gate","bypass gate","remove approval","ignore approval","exfiltrate")
MAX_FILES=int(os.getenv("COMPANYOS_SELF_EVOLUTION_MAX_FILES","4")); MAX_LINES=int(os.getenv("COMPANYOS_SELF_EVOLUTION_MAX_LINES","600")); MAX_DAILY=int(os.getenv("COMPANYOS_SELF_EVOLUTION_MAX_DAILY_PROPOSALS","4"))

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n"); t.replace(p)

def ledger(event,**kw):
    with LEDGER.open("a") as f:f.write(json.dumps({"ts":time.time(),"iso":datetime.now(timezone.utc).isoformat(),"event":event,**kw},sort_keys=True)+"\n")

def run(a,cwd=ROOT,timeout=180,env=None):
    return subprocess.run(a,cwd=str(cwd),env=env or os.environ.copy(),text=True,capture_output=True,timeout=timeout)

def git(a,cwd=ROOT,timeout=120):return run(["git",*a],cwd,timeout)

def dirty(cwd=ROOT):
    out=set()
    for x in git(["status","--porcelain=v1"],cwd).stdout.splitlines():
        if len(x)>=4:
            p=x[3:].split(" -> ")[-1].strip(); out.add(p)
    return out

def path_allowed(rel):
    rel=str(rel).replace("\\","/").lstrip("./"); parts=Path(rel).parts; low=rel.lower()
    if not rel or rel.startswith("/") or ".." in parts:return False,"path_traversal"
    if rel.startswith((".git/",".github/","config/")):return False,"protected_top_level"
    if rel in EXACT_PROTECTED:return False,"exact_protected"
    if any(w in low for w in PROTECTED_WORDS):return False,"protected_path_word"
    if not rel.startswith(SAFE_PREFIXES):return False,"outside_safe_prefix"
    if rel.endswith((".pyc",".pyo",".so",".bin",".zip",".tar",".gz")):return False,"binary_or_archive"
    return True,"allowed"

def changed(cwd):
    a=[x.strip() for x in git(["diff","--name-only","HEAD"],cwd).stdout.splitlines() if x.strip()]
    a += [x.strip() for x in git(["ls-files","--others","--exclude-standard"],cwd).stdout.splitlines() if x.strip()]
    return sorted(set(a))

def guard(cwd,files):
    errors=[]
    if not files:errors.append("no_changes")
    if len(files)>MAX_FILES:errors.append(f"too_many_files:{len(files)}>{MAX_FILES}")
    for rel in files:
        ok,why=path_allowed(rel)
        if not ok:errors.append(f"path_rejected:{rel}:{why}")
    diff=git(["diff","--no-ext-diff","--unified=0","HEAD"],cwd).stdout
    for rel in files:
        if git(["ls-files","--error-unmatch",rel],cwd).returncode!=0:
            p=cwd/rel
            if p.is_file():
                try:diff += "\n+++ "+rel+"\n"+"\n".join("+"+x for x in p.read_text().splitlines())
                except:errors.append(f"unreadable:{rel}")
    lines=sum(1 for x in diff.splitlines() if x[:1] in "+-" and not x.startswith(("+++","---")))
    if lines>MAX_LINES:errors.append(f"too_many_changed_lines:{lines}>{MAX_LINES}")
    low=diff.lower()
    for x in FORBIDDEN:
        if x in low:errors.append("forbidden_fragment:"+x)
    for term in PROTECTED_TERMS:
        if any(x[:1] in "+-" and term in x for x in diff.splitlines()):errors.append("protected_control_touched:"+term)
    return {"ok":not errors,"errors":errors,"changed_files":files,"changed_lines":lines}

def diagnose():
    sup=load(RT/"service_supervisor_state.json",{}); profit=load(RT/"profit_opportunity_runtime_state.json",{})
    services=sup.get("services") or {}; issues=[]; sh={}
    for name,row in services.items():
        sh[name]={"running":bool(row.get("running")),"restarts":int(row.get("restarts") or 0),"consecutive_failures":int(row.get("consecutive_failures") or 0)}
        if not row.get("running"):issues.append("service_not_running:"+name)
        if int(row.get("consecutive_failures") or 0):issues.append("service_failures:"+name)
    goal="Improve the highest-value bottleneck converting researched opportunities into deterministic executable business work with measurable completion and feedback. Improve reliability, execution quality, observability, customer/revenue operations, or agent coordination. Do not touch finance, wallets, credentials, approvals, security gates, connectors, deployment gates, supervisor, or self-evolution guard code."
    if issues:goal="Improve reliability around observed runtime issues: "+", ".join(issues[:8])+". Preserve all protected controls."
    return {"generated_at":time.time(),"services":sh,"issues":issues,"profit_state_present":bool(profit),"recommended_goal":goal,"dirty_files":len(dirty())}

def today_count():
    day=datetime.now(timezone.utc).date().isoformat(); n=0
    if LEDGER.exists():
        for x in LEDGER.read_text(errors="replace").splitlines():
            try:r=json.loads(x); n += int(r.get("event")=="proposal_started" and str(r.get("iso","")).startswith(day))
            except:pass
    return n

def tests(cwd,files):
    rows=[]
    for rel in files:
        if rel.endswith(".py") and (cwd/rel).exists():
            r=run([sys.executable,"-m","py_compile",rel],cwd,60); rows.append({"name":"compile:"+rel,"ok":r.returncode==0,"stderr":(r.stderr or "")[-1200:]})
    if (cwd/"tests/test_self_evolution_guard.py").exists():
        r=run([sys.executable,"-m","unittest","tests.test_self_evolution_guard"],cwd,90); rows.append({"name":"guard_tests","ok":r.returncode==0,"stderr":(r.stderr or "")[-1800:]})
    if os.getenv("COMPANYOS_SELF_EVOLUTION_FULL_TESTS","1")=="1":
        r=run([sys.executable,"-m","unittest","discover","-s","tests","-p","test*.py"],cwd,int(os.getenv("COMPANYOS_SELF_EVOLUTION_TEST_TIMEOUT","240")))
        rows.append({"name":"unittest_discovery","ok":r.returncode==0,"stdout":(r.stdout or "")[-1200:],"stderr":(r.stderr or "")[-1800:]})
    return {"ok":all(x["ok"] for x in rows) if rows else True,"results":rows}

def shadow(run_id):
    branch="companyos-evolution/"+run_id; parent=WT/run_id; wt=parent/"companyos"
    shutil.rmtree(parent,ignore_errors=True); parent.mkdir(parents=True,exist_ok=True)
    r=git(["worktree","add","-b",branch,str(wt),"HEAD"])
    if r.returncode:raise RuntimeError("worktree add failed: "+(r.stderr or r.stdout)[-1500:])
    return wt,branch

def cleanup(wt,branch,keep=False):
    git(["worktree","remove","--force",str(wt)])
    if not keep:git(["branch","-D",branch])

def generate(wt,goal):
    script=wt/"scripts/companyos_adaptive_self_build.py"
    if not script.exists():return {"ok":False,"reason":"adaptive_self_build_missing"}
    home=wt.parent/"home"; home.mkdir(parents=True,exist_ok=True); link=home/"companyos"
    if link.exists() or link.is_symlink():link.unlink()
    link.symlink_to(wt,target_is_directory=True)
    env=os.environ.copy(); env["HOME"]=str(home); env["COMPANYOS_SELF_BUILD_GOAL"]=goal; env["COMPANYOS_SELF_BUILD_EXTERNAL_ACTIONS"]="0"
    env["PYTHONPATH"]=os.pathsep.join([str(wt),str(wt/"scripts"),env.get("PYTHONPATH","")]).strip(os.pathsep)
    r=run([sys.executable,str(script)],wt,int(os.getenv("COMPANYOS_SELF_EVOLUTION_GENERATION_TIMEOUT","420")),env)
    return {"ok":r.returncode==0,"returncode":r.returncode,"stdout_tail":(r.stdout or "")[-3500:],"stderr_tail":(r.stderr or "")[-3500:]}

def commit_candidate(wt,run_id,files):
    git(["add","--",*files],wt); r=git(["commit","-m",f"Self-evolution candidate {run_id}"],wt)
    return git(["rev-parse","HEAD"],wt).stdout.strip() if r.returncode==0 else None

def backup(run_id,files):
    b=BK/run_id; b.mkdir(parents=True,exist_ok=True); meta=[]
    for rel in files:
        src=ROOT/rel; meta.append({"path":rel,"existed":src.exists()})
        if src.is_file():dst=b/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    save(b/"manifest.json",{"files":meta}); return b

def restore(b):
    for x in load(b/"manifest.json",{"files":[]}).get("files",[]):
        rel=x["path"]; dst=ROOT/rel; src=b/rel
        if x.get("existed") and src.exists():dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        elif dst.is_file():dst.unlink()

def promote(run_id,wt,branch,files,csha):
    overlap=sorted(set(files)&dirty())
    if overlap:return {"ok":False,"status":"promotion_pending_overlap","overlap":overlap,"candidate_branch":branch,"candidate_sha":csha}
    patch=git(["diff","HEAD^","HEAD","--binary"],wt).stdout
    chk=subprocess.run(["git","apply","--check","-"],cwd=str(ROOT),input=patch,text=True,capture_output=True)
    if chk.returncode:return {"ok":False,"status":"patch_check_failed","stderr":(chk.stderr or "")[-1800:]}
    b=backup(run_id,files); ap=subprocess.run(["git","apply","-"],cwd=str(ROOT),input=patch,text=True,capture_output=True)
    if ap.returncode:restore(b); return {"ok":False,"status":"apply_failed"}
    t=tests(ROOT,files)
    if not t["ok"]:restore(b); return {"ok":False,"status":"live_tests_failed_rolled_back","tests":t}
    git(["add","--",*files]); c=git(["commit","-m",f"Promote self-evolution candidate {run_id}"])
    if c.returncode:git(["reset","--",*files]); restore(b); return {"ok":False,"status":"commit_failed_rolled_back"}
    sha=git(["rev-parse","HEAD"]).stdout.strip(); push=None
    if os.getenv("COMPANYOS_SELF_EVOLUTION_PUSH","1")=="1":
        br=git(["branch","--show-current"]).stdout.strip()
        if br:push=git(["push","origin",br],timeout=180).returncode==0
    return {"ok":True,"status":"promoted","live_commit":sha,"backup":str(b),"tests":t,"push_ok":push}

def schedule_restart():
    ctl=ROOT/"scripts/companyosctl"
    if os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_RESTART","1")!="1" or not ctl.exists():return False
    subprocess.Popen(["bash","-lc",f"sleep 8; cd {str(ROOT)!r}; scripts/companyosctl restart >/dev/null 2>&1 || true"],cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True); return True

def state_update(**kw):
    s=load(STATE,{}); s.update(kw); s["updated_at"]=time.time(); save(STATE,s); return s

def health_guard():
    s=load(STATE,{}); p=s.get("last_promotion")
    if not isinstance(p,dict):return {"ok":True,"status":"no_recent_promotion"}
    age=time.time()-float(p.get("promoted_at") or 0); window=int(os.getenv("COMPANYOS_SELF_EVOLUTION_GUARD_SECONDS","900"))
    if age>window:
        if not p.get("guard_passed"):p["guard_passed"]=True; s["last_promotion"]=p; save(STATE,s); ledger("promotion_guard_passed",commit=p.get("live_commit"))
        return {"ok":True,"status":"guard_window_passed"}
    sup=load(RT/"service_supervisor_state.json",{}); bad=[n for n,r in (sup.get("services") or {}).items() if not r.get("running") or int(r.get("consecutive_failures") or 0)>=2]
    if not bad:return {"ok":True,"status":"guard_healthy","age_seconds":age}
    commit=p.get("live_commit"); r=git(["revert","--no-edit",commit]) if commit else None
    if not r or r.returncode:git(["revert","--abort"]); state_update(blocked=True,blocked_reason="rollback_conflict"); return {"ok":False,"status":"rollback_conflict_blocked","bad_services":bad}
    rev=git(["rev-parse","HEAD"]).stdout.strip(); ledger("automatic_rollback_complete",reverted_commit=commit,revert_commit=rev,bad_services=bad); state_update(blocked=False,last_rollback={"reverted_commit":commit,"revert_commit":rev,"bad_services":bad,"ts":time.time()},last_promotion=None); schedule_restart(); return {"ok":False,"status":"automatic_rollback_complete","revert_commit":rev,"bad_services":bad}

def cycle(force=False,proposal_only=False):
    if os.getenv("COMPANYOS_ENABLE_SELF_EVOLUTION","0")!="1" and not force:return {"ok":True,"status":"disabled"}
    if load(STATE,{}).get("blocked"):return {"ok":False,"status":"blocked","state":load(STATE,{})}
    hg=health_guard()
    if not hg.get("ok") and "rollback" not in hg.get("status",""):return {"ok":False,"status":"health_guard_blocked","guard":hg}
    if not force and today_count()>=MAX_DAILY:return {"ok":True,"status":"daily_budget_reached","limit":MAX_DAILY}
    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); d=diagnose(); ledger("proposal_started",run_id=run_id,diagnosis=d); state_update(running=True,current_run=run_id,last_diagnosis=d,last_cycle_started=time.time())
    receipt={"run_id":run_id,"started_at":time.time(),"diagnosis":d}; wt=branch=None; keep=False
    try:
        wt,branch=shadow(run_id); receipt["candidate_branch"]=branch
        g=generate(wt,d["recommended_goal"]); receipt["generation"]=g
        if not g["ok"]:receipt["status"]="generation_failed"; return {"ok":False,**receipt}
        files=changed(wt); gd=guard(wt,files); receipt["guard"]=gd
        if not gd["ok"]:receipt["status"]="candidate_rejected_by_guard"; ledger("candidate_rejected",run_id=run_id,guard=gd); return {"ok":False,**receipt}
        t=tests(wt,files); receipt["candidate_tests"]=t
        if not t["ok"]:receipt["status"]="candidate_tests_failed"; return {"ok":False,**receipt}
        csha=commit_candidate(wt,run_id,files); receipt["candidate_sha"]=csha; receipt["changed_files"]=files
        if not csha:receipt["status"]="candidate_commit_failed"; return {"ok":False,**receipt}
        ledger("candidate_qualified",run_id=run_id,candidate_sha=csha,changed_files=files)
        if proposal_only or os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_PROMOTE","1")!="1":keep=True; receipt["status"]="qualified_pending_promotion"; state_update(pending_candidate={"run_id":run_id,"branch":branch,"sha":csha,"changed_files":files}); return {"ok":True,**receipt}
        pr=promote(run_id,wt,branch,files,csha); receipt["promotion"]=pr
        if pr.get("status")=="promotion_pending_overlap":keep=True; receipt["status"]="qualified_pending_overlap"; state_update(pending_candidate={"run_id":run_id,"branch":branch,"sha":csha,"changed_files":files,"overlap":pr.get("overlap")}); return {"ok":True,**receipt}
        if not pr.get("ok"):receipt["status"]=pr.get("status","promotion_failed"); return {"ok":False,**receipt}
        receipt["status"]="promoted"; state_update(pending_candidate=None,last_promotion={"run_id":run_id,"candidate_sha":csha,"live_commit":pr.get("live_commit"),"changed_files":files,"backup":pr.get("backup"),"promoted_at":time.time(),"guard_passed":False}); ledger("promotion_complete",run_id=run_id,live_commit=pr.get("live_commit"),changed_files=files); receipt["restart_scheduled"]=schedule_restart(); return {"ok":True,**receipt}
    except Exception as e:receipt["status"]="exception"; receipt["error"]=f"{type(e).__name__}: {e}"; ledger("cycle_exception",run_id=run_id,error=receipt["error"]); return {"ok":False,**receipt}
    finally:
        receipt["finished_at"]=time.time(); save(RC/f"{run_id}.json",receipt); state_update(running=False,current_run=None,last_cycle_finished=time.time(),last_status=receipt.get("status"),last_receipt=str(RC/f"{run_id}.json"))
        if wt is not None and branch is not None:
            try:cleanup(wt,branch,keep)
            except Exception as e:ledger("worktree_cleanup_failed",run_id=run_id,error=str(e))

def status():
    return {"enabled":os.getenv("COMPANYOS_ENABLE_SELF_EVOLUTION","0")=="1","auto_promote":os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_PROMOTE","1")=="1","auto_restart":os.getenv("COMPANYOS_SELF_EVOLUTION_AUTO_RESTART","1")=="1","max_daily_proposals":MAX_DAILY,"proposals_today":today_count(),"state":load(STATE,{}),"diagnosis":diagnose(),"guard":health_guard()}
