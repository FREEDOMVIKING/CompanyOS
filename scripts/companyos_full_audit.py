from __future__ import annotations
import compileall,json,os,re,subprocess,time,urllib.request
from pathlib import Path
ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"; RT.mkdir(parents=True,exist_ok=True); REPORT=RT/"full_company_audit.json"
checks={}; warnings=[]; failures=[]; details={}
def rec(n,ok,d=None,w=False):
 checks[n]=bool(ok); details[n]=d
 if not ok: (warnings if w else failures).append(n)
def run(*a): return subprocess.run(list(a),cwd=ROOT,text=True,capture_output=True,check=False)
head=run('git','rev-parse','HEAD').stdout.strip(); remote=run('git','rev-parse','origin/main').stdout.strip(); rec('git_main_matches_local_head',head==remote,{'head':head,'origin_main':remote},True)
status=[x for x in run('git','status','--short').stdout.splitlines() if x.strip()]; rec('git_worktree_clean',not status,{'changes':status[:100]},True)
rec('python_companyos_compile',compileall.compile_dir(str(ROOT/'companyos'),quiet=1,force=False))
required=['companyos/runtime/service_supervisor.py','companyos/runtime/runtime_control.py','companyos/runtime/continuous_goal_runtime.py','companyos/runtime/productive_autonomy_watchdog.py','companyos/runtime/dashboard_server.py','companyos/runtime/profit_opportunity_engine.py','companyos/runtime/profit_opportunity_runtime.py']
missing=[x for x in required if not (ROOT/x).exists()]; rec('required_runtime_files_present',not missing,{'missing':missing})
from companyos.runtime.service_supervisor import ServiceSupervisor
from companyos.runtime.runtime_control import UnifiedRuntimeControl
supervised={x.name for x in ServiceSupervisor.default_services()}; expected=set(UnifiedRuntimeControl.EXPECTED_SERVICES); rec('supervisor_matches_health_expectations',supervised==expected,{'supervised':sorted(supervised),'expected':sorted(expected)})
ctl=UnifiedRuntimeControl(ROOT); health=ctl.health(stale_after_seconds=60); rec('runtime_healthy',health.get('healthy'),health)
ps=run('ps','-ef').stdout.splitlines(); needles={'supervisor':'service_supervisor.py','goal':'continuous_goal_runtime','watchdog':'productive_autonomy_watchdog','dashboard':'dashboard_server','profit':'profit_opportunity_runtime'}; counts={k:sum(1 for line in ps if v in line and 'grep' not in line) for k,v in needles.items()}; rec('no_duplicate_core_processes',all(v<=1 for v in counts.values()),counts)
try:
 with urllib.request.urlopen('http://127.0.0.1:8765/api/status',timeout=5) as r: dash=json.loads(r.read().decode()); ok=r.status==200
except Exception as e: dash={'error':f'{type(e).__name__}:{e}'}; ok=False
rec('dashboard_reachable',ok,dash)
try:
 from companyos.runtime.profit_opportunity_engine import choose
 d=choose(); rec('profit_engine_operational',isinstance(d,dict),d)
 stale=[]
 for row in (d.get('ranked') or [])[:50]:
  src=str(row.get('source','')).lower()
  if any(x in src for x in ('test','sample','validation_report')): stale.append({'name':row.get('name'),'source':src})
 rec('profit_engine_stale_artifact_isolation',not stale,{'stale_ranked_entries':stale[:20]},True)
except Exception as e: rec('profit_engine_operational',False,{'error':repr(e)})
try:
 from companyos.runtime.connector_readiness import ConnectorReadinessAudit
 rec('connector_audit_operational',True,ConnectorReadinessAudit(ROOT).run())
except Exception as e: rec('connector_audit_operational',False,{'error':repr(e)},True)
finance={'live_enabled':os.getenv('COMPANYOS_ENABLE_LIVE_FINANCE','0')=='1','daily_cap':os.getenv('COMPANYOS_DAILY_FINANCE_CAP_USD'),'single_cap':os.getenv('COMPANYOS_SINGLE_FINANCE_CAP_USD'),'min_transaction':os.getenv('COMPANYOS_MIN_TRANSACTION_AMOUNT')}; rec('finance_limits_configured',all(finance[k] for k in ('daily_cap','single_cap','min_transaction')),finance,True)
tracked=run('git','ls-files').stdout.splitlines(); risky=[]
for rel in tracked:
 low=rel.lower(); base=Path(low).name
 if (base=='.env' or base.startswith('.env.')) and not base.endswith(('.example','.sample','.template')): risky.append(rel)
 if low.endswith(('.pem','.p12','.pfx','.key','.secret')): risky.append(rel)
rec('no_tracked_credential_files',not risky,{'files':sorted(set(risky))})
rx=[re.compile(r'sk-[A-Za-z0-9_-]{20,}'),re.compile(r'AKIA[0-9A-Z]{16}'),re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]; hits=[]
for rel in tracked:
 p=ROOT/rel
 if not p.is_file() or p.suffix.lower() in {'.png','.jpg','.jpeg','.gif','.zip','.gz','.tar','.sqlite','.sqlite3','.pyc'}: continue
 try: t=p.read_text(encoding='utf-8',errors='ignore')
 except: continue
 if any(r.search(t) for r in rx): hits.append(rel)
rec('no_obvious_literal_secrets_in_tracked_text',not hits,{'files':hits[:100]})
errors=[]
for p in [RT/'service_supervisor.log',RT/'runtime_control.log',RT/'productive_autonomy_watchdog.log',RT/'profit_opportunity_runtime.log']:
 if not p.exists(): continue
 for line in p.read_text(encoding='utf-8',errors='replace').splitlines()[-1500:]:
  if re.search(r'\b(traceback|fatal|unhandled exception)\b',line,re.I): errors.append({'log':p.name,'line':line[-500:]})
rec('no_recent_fatal_log_errors',not errors,{'hits':errors[-30:]},True)
score=max(0,100-12*len(failures)-3*len(warnings)); verdict='FAIL' if failures else 'PASS_WITH_WARNINGS' if warnings else 'PASS'; out={'generated_at_unix':time.time(),'head':head,'verdict':verdict,'score':score,'checks':checks,'failures':failures,'warnings':warnings,'details':details}; REPORT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n')
print('===== COMPANYOS FULL COMPANY AUDIT ====='); print('verdict:',verdict); print('score:',score); print('failures:',failures); print('warnings:',warnings); print('runtime_healthy:',checks.get('runtime_healthy')); print('dashboard_reachable:',checks.get('dashboard_reachable')); print('profit_engine_operational:',checks.get('profit_engine_operational')); print('report:',REPORT)
raise SystemExit(0 if verdict!='FAIL' else 50)
