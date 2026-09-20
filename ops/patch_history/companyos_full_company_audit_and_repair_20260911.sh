#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
cd "$ROOT"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/backups/full_company_audit_$STAMP"
mkdir -p "$BACKUP/companyos/runtime" "$BACKUP/scripts"

for f in companyos/runtime/service_supervisor.py companyos/runtime/runtime_control.py companyos/runtime/dashboard_server.py scripts/companyos_full_audit.py; do
  if [ -e "$f" ]; then mkdir -p "$BACKUP/$(dirname "$f")"; cp -a "$f" "$BACKUP/$f"; fi
done

echo '===== RECONCILE DASHBOARD ====='
if [ ! -f companyos/runtime/dashboard_server.py ]; then
cat > companyos/runtime/dashboard_server.py <<'PY'
from __future__ import annotations
import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"; RT.mkdir(parents=True,exist_ok=True)
HOST=os.getenv("COMPANYOS_DASHBOARD_HOST","127.0.0.1"); PORT=int(os.getenv("COMPANYOS_DASHBOARD_PORT","8765")); TOKEN=os.getenv("COMPANYOS_DASHBOARD_TOKEN","")
if HOST not in {"127.0.0.1","localhost","::1"} and not TOKEN: raise SystemExit("Refusing non-local dashboard bind without token")
HTML='<!doctype html><html><body style="background:#111;color:#eee;font-family:system-ui"><h1>CompanyOS</h1><button onclick="a(\'start\')">Start</button><button onclick="a(\'stop\')">Stop</button><button onclick="a(\'restart\')">Restart</button><button onclick="a(\'recover\')">Recover</button><pre id="o"></pre><script>async function r(){let x=await fetch("/api/status");o.textContent=JSON.stringify(await x.json(),null,2)}async function a(x){await fetch("/api/control/"+x,{method:"POST"});setTimeout(r,700)}r();setInterval(r,5000)</script></body></html>'
def auth(h): return (not TOKEN) or h.headers.get("X-CompanyOS-Token","")==TOKEN
def status():
 from companyos.runtime.runtime_control import UnifiedRuntimeControl
 out={"checked_at_unix":time.time(),"health":UnifiedRuntimeControl(ROOT).health()}
 try:
  from companyos.runtime.profit_opportunity_engine import choose
  out["profit_engine"]=choose()
 except Exception as e: out["profit_engine"]={"error":f"{type(e).__name__}:{e}"}
 return out
class H(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def sendj(self,c,o):
  d=json.dumps(o,indent=2,default=str).encode(); self.send_response(c); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d)
 def do_GET(self):
  p=urlparse(self.path).path
  if p=="/":
   d=HTML.encode(); self.send_response(200); self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d); return
  if p in {"/api/status","/api/health"}:
   if not auth(self): return self.sendj(401,{"ok":False})
   return self.sendj(200,status())
  self.sendj(404,{"ok":False})
 def do_POST(self):
  if not auth(self): return self.sendj(401,{"ok":False})
  p=urlparse(self.path).path
  if not p.startswith("/api/control/"): return self.sendj(404,{"ok":False})
  from companyos.runtime.runtime_control import UnifiedRuntimeControl
  c=UnifiedRuntimeControl(ROOT); x=p.rsplit("/",1)[-1]; fn={"start":c.start,"stop":c.stop,"restart":c.restart,"recover":c.recover}.get(x)
  if not fn: return self.sendj(400,{"ok":False})
  z=fn(); self.sendj(200 if z.get("ok") else 500,z)
def main():
 (RT/"dashboard_server_state.json").write_text(json.dumps({"pid":os.getpid(),"host":HOST,"port":PORT,"started_at_unix":time.time()},indent=2)+"\n")
 ThreadingHTTPServer((HOST,PORT),H).serve_forever()
if __name__=="__main__": main()
PY
fi

echo '===== RECONCILE SUPERVISOR ====='
python - <<'PY'
from pathlib import Path
p=Path('companyos/runtime/service_supervisor.py'); s=p.read_text()
start=s.index('    @staticmethod\n    def default_services()'); end=s.index('\n    def _log(',start)
rep='''    @staticmethod
    def default_services() -> list[ManagedService]:
        python = sys.executable
        services = [
            ManagedService("continuous_goal_runtime", (python, "-c", "from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime; ContinuousGoalRuntime().run()")),
            ManagedService("productive_autonomy_watchdog", (python, "-m", "companyos.runtime.productive_autonomy_watchdog")),
            ManagedService("local_dashboard", (python, "-m", "companyos.runtime.dashboard_server")),
        ]
        if (Path.home()/"companyos/companyos/runtime/profit_opportunity_runtime.py").exists():
            services.append(ManagedService("profit_opportunity_runtime", (python, "-m", "companyos.runtime.profit_opportunity_runtime")))
        return services
'''
p.write_text(s[:start]+rep+s[end:])
PY

python - <<'PY'
from pathlib import Path
p=Path('companyos/runtime/runtime_control.py'); s=p.read_text()
old='''    EXPECTED_SERVICES = {
        "continuous_goal_runtime",
        "productive_autonomy_watchdog",
        "local_dashboard",
    }
'''
new='''    EXPECTED_SERVICES = {
        "continuous_goal_runtime",
        "productive_autonomy_watchdog",
        "local_dashboard",
        "profit_opportunity_runtime",
    }
'''
if old in s: s=s.replace(old,new,1)
elif '"profit_opportunity_runtime"' not in s: raise SystemExit('EXPECTED_SERVICES block not found')
p.write_text(s)
PY

if [ -f .companyos_runtime/profit_engine.pid ]; then
  P="$(cat .companyos_runtime/profit_engine.pid 2>/dev/null || true)"; [ -z "$P" ] || kill "$P" 2>/dev/null || true; rm -f .companyos_runtime/profit_engine.pid
fi

cat > scripts/companyos_full_audit.py <<'PY'
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
PY
chmod +x scripts/companyos_full_audit.py

python -m py_compile companyos/runtime/service_supervisor.py companyos/runtime/runtime_control.py companyos/runtime/dashboard_server.py companyos/runtime/profit_opportunity_engine.py companyos/runtime/profit_opportunity_runtime.py scripts/companyos_full_audit.py

echo '===== RESTART FULL STACK ====='
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 2
scripts/companyosctl start
sleep 5

echo '===== RUN AUDIT ====='
set +e
PYTHONPATH="$ROOT" python scripts/companyos_full_audit.py
RC=$?
set -e

echo '===== COMMIT + PUSH ====='
git add companyos/runtime/service_supervisor.py companyos/runtime/runtime_control.py companyos/runtime/dashboard_server.py scripts/companyos_full_audit.py
git commit -m 'Reconcile CompanyOS supervised stack and add full company audit' || true
git push origin HEAD
git push origin HEAD:main
git fetch origin main

echo '===== FINAL SUMMARY ====='
python - <<'PY'
import json
from pathlib import Path
x=json.loads((Path.home()/"companyos/.companyos_runtime/full_company_audit.json").read_text())
print('verdict:',x.get('verdict')); print('score:',x.get('score')); print('failures:',x.get('failures')); print('warnings:',x.get('warnings'))
PY
scripts/companyosctl health || true
[ "$RC" -eq 0 ] && echo 'COMPANYOS_FULL_COMPANY_AUDIT=PASS' || echo 'COMPANYOS_FULL_COMPANY_AUDIT=NEEDS_ATTENTION'
