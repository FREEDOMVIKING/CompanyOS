#!/data/data/com.termux/files/usr/bin/bash
# CompanyOS full source sync + whole-project audit
# Designed for the authoritative Termux checkout at ~/companyos.
set -uo pipefail

ROOT="$HOME/companyos"
RUNTIME="$HOME/.companyos_runtime"
EXPECTED_REMOTE="github.com/FREEDOMVIKING/CompanyOS"
STAMP="$(date +%Y%m%d_%H%M%S)"
AUDIT_DIR="$ROOT/audit"
LOCAL_AUDIT_DIR="$RUNTIME/audit_logs/$STAMP"
REPORT_JSON="$AUDIT_DIR/COMPANYOS_FULL_AUDIT_LATEST.json"
REPORT_MD="$AUDIT_DIR/COMPANYOS_FULL_AUDIT_LATEST.md"

mkdir -p "$AUDIT_DIR" "$LOCAL_AUDIT_DIR"

say(){ printf '%s\n' "$*"; }
die(){ say "FULL_SYNC_AUDIT_ABORT=$*"; exit 1; }

[ -d "$ROOT/.git" ] || die "not_a_git_repo:$ROOT"
cd "$ROOT" || die "cannot_cd_repo"

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

say "===== COMPANYOS FULL GITHUB SYNC + TOTAL AUDIT ====="
say "STAMP=$STAMP"
say "REPO=$ROOT"
say "RUNTIME=$RUNTIME"
say "GITHUB=FREEDOMVIKING/CompanyOS"
say "NOTE=SOURCE_AND_SAFE_PATCH_HISTORY_ONLY"
say "NOTE=RUNTIME_STATE_SECRETS_WALLETS_AND_CREDENTIALS_ARE_NOT_COMMITTED"
say "NOTE=NO_FINANCIAL_ACTIONS"
say "NOTE=NO_EMAIL_OR_CUSTOMER_OUTREACH"
say "NOTE=NO_DEPLOYMENT_OR_PURCHASES"
say ""

# ------------------------------------------------------------
# 1) Verify repository / branch / remote.
# ------------------------------------------------------------
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
BRANCH="$(git branch --show-current 2>/dev/null || true)"
[ -n "$BRANCH" ] || die "detached_head"
[ -n "$REMOTE_URL" ] || die "origin_remote_missing"

case "$REMOTE_URL" in
  *"$EXPECTED_REMOTE"*|*"github.com:FREEDOMVIKING/CompanyOS"*) ;;
  *) die "unexpected_origin:$REMOTE_URL" ;;
esac

say "BRANCH=$BRANCH"
say "ORIGIN=$REMOTE_URL"

# Keep this audit tool itself in the repository for reproducibility.
mkdir -p "$ROOT/scripts"
if [ -f "$0" ]; then
  SELF_REAL="$(cd "$(dirname "$0")" 2>/dev/null && pwd)/$(basename "$0")"
  TARGET_REAL="$ROOT/scripts/companyos_full_sync_audit.sh"
  if [ "$SELF_REAL" != "$TARGET_REAL" ]; then
    cp "$0" "$TARGET_REAL" 2>/dev/null || true
    chmod +x "$TARGET_REAL" 2>/dev/null || true
  fi
fi

# ------------------------------------------------------------
# 2) Preserve safe CompanyOS patch/install scripts from Downloads/Home.
#    These are source-history artifacts, not runtime state.
# ------------------------------------------------------------
say "===== ARCHIVE SAFE LOCAL PATCH HISTORY ====="
mkdir -p "$ROOT/ops/patch_history"

python - <<'PY'
from pathlib import Path
import hashlib,re,shutil,os

home=Path.home()
root=home/"companyos"
dest=root/"ops/patch_history"

# V67.2: patch/build history is no longer copied into the active branch by default.
# Git history and recovery branches preserve prior artifacts.
if os.getenv("COMPANYOS_COMMIT_PATCH_HISTORY","0") != "1":
    print("PATCH_HISTORY_IMPORT=DISABLED_BY_DEFAULT")
    print("PATCH_HISTORY_IMPORT_OVERRIDE=COMPANYOS_COMMIT_PATCH_HISTORY=1")
    raise SystemExit(0)

dest.mkdir(parents=True,exist_ok=True)

sources=[home]
downloads=home/"storage/downloads"
if downloads.exists():
    sources.append(downloads)

patterns=(
    "companyos_v*.sh",
    "companyos_*202609*.sh",
    "companyos_*audit*.sh",
    "companyos_*launch*.sh",
)

secret_res=[
    re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"(?i)\b(?:SOLANA_PRIVATE_KEY|SMTP_PASSWORD)\s*=\s*['\"]?[A-Za-z0-9+/=_-]{16,}"),
]

found={}
skipped=[]
for src in sources:
    for pat in patterns:
        for p in src.glob(pat):
            try:
                if not p.is_file() or p.stat().st_size <= 0 or p.stat().st_size > 2_000_000:
                    continue
                raw=p.read_bytes()
            except Exception:
                continue
            if any(rx.search(raw) for rx in secret_res):
                skipped.append(p.name)
                continue
            h=hashlib.sha256(raw).hexdigest()
            prev=found.get(p.name)
            if prev is None or p.stat().st_mtime > prev[0]:
                found[p.name]=(p.stat().st_mtime,p,h)

copied=0
for name,(_,p,h) in sorted(found.items()):
    out=dest/name
    try:
        if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest()==h:
            continue
        shutil.copy2(p,out)
        os.chmod(out,0o755)
        copied+=1
    except Exception:
        pass

print(f"PATCH_HISTORY_NEW_OR_UPDATED={copied}")
print(f"PATCH_HISTORY_TOTAL={len(list(dest.glob('*.sh')))}")
print(f"PATCH_HISTORY_SECRET_SUSPECT_SKIPPED={len(skipped)}")
PY

# ------------------------------------------------------------
# 3) Stage the complete project, then explicitly unstage runtime/private state.
# ------------------------------------------------------------
say "===== STAGE COMPLETE PROJECT SOURCE ====="
git add -A -- .

# Never push mutable runtime state or local credentials just because they exist.
# `git reset` only unstages changes; it does not delete local files.
for p in \
  ".env" ".env.local" ".companyos_launch_env" \
  "companyos_runtime/connectors/actions.json" \
  "companyos_runtime/connectors/executions.json" \
  "companyos_runtime/connectors/dead_letter.json" \
  "companyos_runtime/connectors/dead_letter.jsonl"
do
  if git ls-files --error-unmatch "$p" >/dev/null 2>&1 || [ -e "$p" ]; then
    git reset -q HEAD -- "$p" >/dev/null 2>&1 || true
  fi
done

# Unstage obvious local/runtime artifacts if any slipped into the worktree.
while IFS= read -r p; do
  [ -n "$p" ] || continue
  case "$p" in
    .companyos_runtime/*|*/__pycache__/*|*.pyc|*.pyo|*.log|*.sqlite|*.sqlite3|*.db|*.pid|*.sock|*.pem|*.key)
      git reset -q HEAD -- "$p" >/dev/null 2>&1 || true
      ;;
  esac
done < <(git diff --cached --name-only)

# ------------------------------------------------------------
# 4) Public-repo secret gate. It reports file/line/type only, never values.
# ------------------------------------------------------------
say "===== PUBLIC REPOSITORY SECRET GATE ====="
python - <<'PY'
from pathlib import Path
import subprocess,re,sys

root=Path.home()/"companyos"

def cmd(args):
    return subprocess.run(args,cwd=root,text=True,capture_output=True).stdout.splitlines()

staged=cmd(["git","diff","--cached","--name-only","--diff-filter=ACMR"])
danger_name=re.compile(
    r"(^|/)(?:\.env(?:\.|$)|id_rsa(?:\.pub)?$|credentials?(?:\.json)?$|secrets?(?:\.json)?$|"
    r"wallet(?:_keypair)?(?:\.json)?$|.*private.*\.(?:pem|key|json)$)",
    re.I,
)
allowed_name=re.compile(r"(?:example|sample|template|fixture|test)",re.I)

patterns=[
    ("OPENAI_KEY",re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("GITHUB_TOKEN",re.compile(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}")),
    ("PRIVATE_KEY_BLOCK",re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("SOLANA_PRIVATE_KEY",re.compile(r"(?i)\bSOLANA_PRIVATE_KEY\s*=\s*['\"]?([^\s#'\"]{16,})")),
    ("SMTP_PASSWORD",re.compile(r"(?i)\bSMTP_PASSWORD\s*=\s*['\"]?([^\s#'\"]{8,})")),
]

hits=[]
for rel in staged:
    if danger_name.search(rel) and not allowed_name.search(rel):
        hits.append((rel,0,"SENSITIVE_FILENAME"))
        continue
    p=root/rel
    try:
        if not p.is_file() or p.stat().st_size>3_000_000:
            continue
        text=p.read_text(errors="ignore")
    except Exception:
        continue
    for n,line in enumerate(text.splitlines(),1):
        for kind,rx in patterns:
            if rx.search(line):
                low=line.lower()
                if any(x in low for x in ("example","placeholder","changeme","dummy","test_key","your_key")):
                    continue
                hits.append((rel,n,kind))

if hits:
    print("SECRET_GATE=BLOCK")
    for rel,n,kind in hits[:100]:
        print(f"SECRET_RISK_FILE={rel} LINE={n} TYPE={kind}")
    sys.exit(42)

print("SECRET_GATE=PASS")
print(f"STAGED_FILES_SCANNED={len(staged)}")
PY
SECRET_RC=$?
if [ "$SECRET_RC" -ne 0 ]; then
  say "PUSH_SKIPPED=SECRET_GATE_BLOCKED"
  say "Nothing new was pushed. Review the reported file names; no secret values were printed."
  exit "$SECRET_RC"
fi

say "===== STAGED SUMMARY ====="
git --no-pager diff --cached --stat || true

# ------------------------------------------------------------
# 5) Commit + safe sync + push current branch.
# ------------------------------------------------------------
say "===== FIRST GITHUB PUSH: CURRENT PROJECT STATE ====="
PRE_PUSH_SHA="$(git rev-parse HEAD)"

if ! git diff --cached --quiet; then
  git commit -m "Sync full CompanyOS state before comprehensive audit" || die "git_commit_failed"
else
  say "SOURCE_COMMIT=NO_CHANGES"
fi

SOURCE_SHA="$(git rev-parse HEAD)"
say "SOURCE_SHA=$SOURCE_SHA"

# Fetch and rebase only when necessary; preserve a local recovery branch first.
git fetch origin "$BRANCH" >/dev/null 2>&1 || true
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  COUNTS="$(git rev-list --left-right --count "origin/$BRANCH...HEAD" 2>/dev/null || echo "0 0")"
  BEHIND="$(printf '%s' "$COUNTS" | awk '{print $1}')"
  AHEAD="$(printf '%s' "$COUNTS" | awk '{print $2}')"
  say "REMOTE_COMPARE_BEHIND=$BEHIND"
  say "REMOTE_COMPARE_AHEAD=$AHEAD"
  if [ "${BEHIND:-0}" -gt 0 ]; then
    BACKUP_BRANCH="backup/pre-full-audit-$STAMP"
    git branch "$BACKUP_BRANCH" HEAD >/dev/null 2>&1 || true
    say "LOCAL_RECOVERY_BRANCH=$BACKUP_BRANCH"
    if ! git rebase "origin/$BRANCH"; then
      git rebase --abort >/dev/null 2>&1 || true
      die "remote_diverged_rebase_failed_recovery_branch:$BACKUP_BRANCH"
    fi
  fi
fi

git push origin "HEAD:$BRANCH" || die "source_push_failed"
SOURCE_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}' | head -1)"
[ "$REMOTE_SHA" = "$SOURCE_SHA" ] || die "remote_sha_mismatch_after_source_push"
say "SOURCE_PUSH_VERIFIED=PASS"

# ------------------------------------------------------------
# 6) Comprehensive read-only audit.
#    Detailed command logs stay local under ~/.companyos_runtime.
# ------------------------------------------------------------
say "===== FULL COMPANY AUDIT ====="

export COMPANYOS_AUDIT_STAMP="$STAMP"
export COMPANYOS_AUDIT_BRANCH="$BRANCH"
export COMPANYOS_AUDIT_SOURCE_SHA="$SOURCE_SHA"
export COMPANYOS_AUDIT_LOCAL_DIR="$LOCAL_AUDIT_DIR"
export COMPANYOS_AUDIT_REPORT_JSON="$REPORT_JSON"
export COMPANYOS_AUDIT_REPORT_MD="$REPORT_MD"

python - <<'PY'
from __future__ import annotations
from pathlib import Path
from collections import Counter,defaultdict
import subprocess, json, os, re, time, hashlib, traceback, shlex

HOME=Path.home()
ROOT=HOME/"companyos"
RT=HOME/".companyos_runtime"
STAMP=os.environ["COMPANYOS_AUDIT_STAMP"]
BRANCH=os.environ["COMPANYOS_AUDIT_BRANCH"]
SOURCE_SHA=os.environ["COMPANYOS_AUDIT_SOURCE_SHA"]
LOGDIR=Path(os.environ["COMPANYOS_AUDIT_LOCAL_DIR"])
REPORT_JSON=Path(os.environ["COMPANYOS_AUDIT_REPORT_JSON"])
REPORT_MD=Path(os.environ["COMPANYOS_AUDIT_REPORT_MD"])
LOGDIR.mkdir(parents=True,exist_ok=True)
REPORT_JSON.parent.mkdir(parents=True,exist_ok=True)

audit={
    "schema":"companyos.full_total_audit.v1",
    "timestamp_unix":time.time(),
    "timestamp_local":time.strftime("%Y-%m-%d %H:%M:%S"),
    "repository":"FREEDOMVIKING/CompanyOS",
    "branch":BRANCH,
    "source_snapshot_sha":SOURCE_SHA,
    "mode":"READ_ONLY_AUDIT",
    "external_actions_performed":False,
    "financial_actions_performed":False,
    "email_actions_performed":False,
    "deployment_actions_performed":False,
    "checks":{},
    "inventory":{},
    "runtime":{},
    "security":{},
    "finance_policy_scan":{},
    "capabilities":{},
    "warnings":[],
    "failures":[],
}

def run(name,argv,timeout=180,cwd=ROOT):
    log=LOGDIR/f"{name}.log"
    rec={"command":" ".join(shlex.quote(str(x)) for x in argv),"timeout_seconds":timeout}
    try:
        cp=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,timeout=timeout,env=os.environ.copy())
        out=(cp.stdout or "")+"\n"+(cp.stderr or "")
        log.write_text(out,errors="ignore")
        rec.update({"returncode":cp.returncode,"passed":cp.returncode==0,"log":str(log)})
    except subprocess.TimeoutExpired as exc:
        text=(exc.stdout or "")
        if isinstance(text,bytes): text=text.decode(errors="ignore")
        err=(exc.stderr or "")
        if isinstance(err,bytes): err=err.decode(errors="ignore")
        log.write_text(text+"\n"+err,errors="ignore")
        rec.update({"returncode":124,"passed":False,"timed_out":True,"log":str(log)})
    except Exception as exc:
        log.write_text(f"{type(exc).__name__}: {exc}\n")
        rec.update({"returncode":125,"passed":False,"error":f"{type(exc).__name__}: {exc}","log":str(log)})
    audit["checks"][name]=rec
    return rec

def git(*args):
    cp=subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True)
    return cp.stdout.strip()

# ---------- repository inventory ----------
tracked=git("ls-files").splitlines()
ext=Counter()
loc=Counter()
bytes_total=0
for rel in tracked:
    p=ROOT/rel
    if not p.is_file():
        continue
    try:
        st=p.stat(); bytes_total+=st.st_size
    except Exception:
        pass
    suffix=p.suffix.lower() or "<none>"
    ext[suffix]+=1
    if suffix in {".py",".sh",".js",".ts",".tsx",".jsx",".html",".css",".json",".yaml",".yml",".toml",".md"}:
        try:
            loc[suffix]+=sum(1 for _ in p.open(errors="ignore"))
        except Exception:
            pass

audit["inventory"].update({
    "tracked_files":len(tracked),
    "tracked_bytes":bytes_total,
    "extensions":dict(ext.most_common()),
    "lines_by_extension":dict(loc.most_common()),
    "python_files":ext.get(".py",0),
    "shell_files":ext.get(".sh",0),
    "test_files":sum(1 for x in tracked if x.startswith("tests/") and x.endswith(".py")),
    "script_files":sum(1 for x in tracked if x.startswith("scripts/")),
    "patch_history_files":sum(1 for x in tracked if x.startswith("ops/patch_history/")),
    "commit_count":int(git("rev-list","--count","HEAD") or 0),
    "head_sha":git("rev-parse","HEAD"),
    "head_subject":git("log","-1","--pretty=%s"),
    "head_time":git("log","-1","--pretty=%cI"),
    "git_status_porcelain":git("status","--porcelain").splitlines(),
})

# Current vs main / remote current branch.
run("git_fetch_audit",["git","fetch","origin"],120)
for refname,key in ((f"origin/{BRANCH}","current_branch"),("origin/main","main")):
    cp=subprocess.run(["git","rev-parse","--verify",refname],cwd=ROOT,text=True,capture_output=True)
    if cp.returncode==0:
        audit["inventory"][f"{key}_remote_sha"]=cp.stdout.strip()

if "main_remote_sha" in audit["inventory"]:
    cmp=subprocess.run(
        ["git","rev-list","--left-right","--count",f"origin/main...HEAD"],
        cwd=ROOT,text=True,capture_output=True
    )
    if cmp.returncode==0:
        vals=cmp.stdout.split()
        if len(vals)==2:
            audit["inventory"]["vs_main_behind"]=int(vals[0])
            audit["inventory"]["vs_main_ahead"]=int(vals[1])

# Latest V-style markers observed in tracked source.
versions=set()
vrx=re.compile(r"\bV(\d+)\.(\d+(?:\.\d+)*)\b",re.I)
for rel in tracked:
    p=ROOT/rel
    if p.suffix.lower() not in {".py",".sh",".md",".json",".txt"}:
        continue
    try:
        if p.stat().st_size>1_500_000: continue
        text=p.read_text(errors="ignore")
    except Exception:
        continue
    for m in vrx.finditer(text):
        versions.add("V"+m.group(1)+"."+m.group(2))
def version_key(v):
    nums=[]
    for part in v[1:].split("."):
        m=re.match(r"(\d+)",part)
        nums.append(int(m.group(1)) if m else 0)
    return tuple(nums)
audit["inventory"]["latest_version_markers"]=sorted(versions,key=version_key,reverse=True)[:25]

# ---------- source integrity ----------
run("python_compileall",["python","-m","compileall","-q","companyos"],300)

# Shell syntax for every tracked shell script, one by one, low memory.
shell_bad=[]
shell_checked=0
for rel in tracked:
    if not rel.endswith(".sh"): continue
    shell_checked+=1
    cp=subprocess.run(["bash","-n",rel],cwd=ROOT,text=True,capture_output=True)
    if cp.returncode!=0:
        shell_bad.append({"file":rel,"returncode":cp.returncode})
audit["checks"]["shell_syntax_all"]={
    "passed":not shell_bad,
    "checked":shell_checked,
    "failed_count":len(shell_bad),
    "failed_files":shell_bad[:100],
}

# Full pytest, sequential and bounded. No xdist parallelism.
run("pytest_full",["python","-m","pytest","-q","--disable-warnings","--maxfail=25"],900)

# Existing project-native audits/health checks if present.
native=[
    ("native_full_launch_validation",["python","scripts/validate_companyos_full_launch.py"],240),
    ("native_launch_audit",["scripts/companyos_launchctl","audit"],180),
    ("native_launch_snapshot",["scripts/companyos_launchctl","snapshot"],180),
    ("native_qualify",["scripts/companyos_qualify"],240),
    ("native_company_health",["scripts/companyosctl","health"],120),
    ("native_company_status",["scripts/companyosctl","status"],120),
]
for name,argv,timeout in native:
    p=ROOT/argv[0] if "/" in argv[0] else None
    if p is not None and not p.exists():
        audit["checks"][name]={"passed":None,"skipped":"tool_not_present"}
        continue
    run(name,argv,timeout)

# ---------- runtime queue ----------
queue_summary={}
try:
    from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
    q=AutonomousTaskQueue()
    tasks=list(q._iter_task_files())
    states=Counter(str(getattr(t,"state","UNKNOWN")) for t in tasks)
    types=Counter(str(getattr(t,"task_type","UNKNOWN")) for t in tasks)
    queue_summary={
        "total_records":len(tasks),
        "states":dict(states),
        "types_top20":dict(types.most_common(20)),
        "queued":states.get("QUEUED",0),
        "running":states.get("RUNNING",0),
        "claimed":states.get("CLAIMED",0),
        "completed":states.get("COMPLETED",0),
        "failed":states.get("FAILED",0),
        "cancelled":states.get("CANCELLED",0),
    }
except Exception as exc:
    queue_summary={"error":f"{type(exc).__name__}: {exc}"}
audit["runtime"]["task_queue"]=queue_summary

# ---------- venture inventory ----------
venture_summary={}
try:
    from companyos.governance.venture_identity_progression import candidate_ventures, evaluate_all
    candidates=candidate_ventures()
    evaluated=evaluate_all()
    rows=[]
    if isinstance(evaluated,dict):
        iterable=evaluated.items()
    elif isinstance(evaluated,list):
        iterable=[(str(i),x) for i,x in enumerate(evaluated)]
    else:
        iterable=[]
    stages=Counter()
    for key,row in iterable:
        if not isinstance(row,dict): continue
        stage=str(row.get("stage") or row.get("inferred_stage") or "UNKNOWN")
        stages[stage]+=1
        rows.append({
            "id":row.get("canonical_id") or row.get("venture_id") or key,
            "stage":stage,
            "artifact_count":row.get("artifact_count"),
            "unchanged_observations":row.get("unchanged_observations"),
        })
    venture_summary={
        "canonical_candidate_count":len(candidates) if isinstance(candidates,dict) else None,
        "evaluated_count":len(rows),
        "stages":dict(stages),
        "ventures":rows[:100],
    }
except Exception as exc:
    venture_summary={"error":f"{type(exc).__name__}: {exc}"}
audit["runtime"]["ventures"]=venture_summary

# ---------- connector readiness (health only; no actions) ----------
try:
    from companyos.connectors_live.engine import ConnectorEngine
    h=ConnectorEngine().health()
    connectors=(h.get("connectors") or {}) if isinstance(h,dict) else {}
    safe={}
    for name,row in connectors.items():
        if not isinstance(row,dict): continue
        safe[name]={
            k:row.get(k) for k in ("configured","enabled","healthy","status","ready")
            if k in row
        }
    audit["runtime"]["connectors"]=safe
except Exception as exc:
    audit["runtime"]["connectors"]={"error":f"{type(exc).__name__}: {exc}"}

# ---------- live authority flags ----------
try:
    from companyos.runtime.live_drl_strategy_governor import LIVE_AUTHORITY
    audit["runtime"]["authority_switches"]={str(k):bool(v) for k,v in LIVE_AUTHORITY.items()}
except Exception as exc:
    audit["runtime"]["authority_switches"]={"error":f"{type(exc).__name__}: {exc}"}

# ---------- running processes (names/commands only, no env) ----------
try:
    cp=subprocess.run(["ps","-A","-o","pid,args"],text=True,capture_output=True,timeout=20)
    rows=[]
    for line in cp.stdout.splitlines():
        if "companyos" in line.lower():
            rows.append(" ".join(line.split())[:500])
    audit["runtime"]["companyos_processes"]=rows[:100]
    audit["runtime"]["companyos_process_count"]=len(rows)
except Exception as exc:
    audit["runtime"]["companyos_processes_error"]=f"{type(exc).__name__}: {exc}"

# ---------- previous audit / reports ----------
for p in (
    RT/"full_company_audit.json",
    RT/"verified_web_prospect_discovery_latest.json",
    RT/"customer_acquisition_bridge_latest.json",
    RT/"venture_liveness_latest.json",
):
    if not p.exists(): continue
    try:
        d=json.loads(p.read_text())
        # only non-secret summary keys
        audit["runtime"].setdefault("latest_runtime_reports",{})[p.name]={
            k:d.get(k) for k in (
                "version","status","mode","healthy","ready","verified_contacts_created",
                "timestamp_unix","reason","progression_mode"
            ) if k in d
        }
    except Exception:
        pass

# ---------- capability presence inventory ----------
capability_paths={
    "autonomous_task_queue":"companyos/runtime/autonomous_task_queue.py",
    "task_dispatcher":"companyos/runtime/autonomous_task_dispatcher.py",
    "specialist_registry":"companyos/runtime/default_specialist_registry.py",
    "self_evolution":"companyos/runtime/self_evolution_engine.py",
    "profit_opportunity_engine":"companyos/runtime/profit_opportunity_engine.py",
    "customer_acquisition":"companyos/runtime/customer_acquisition_bridge.py",
    "verified_web_prospect_discovery":"companyos/runtime/verified_web_prospect_discovery.py",
    "venture_liveness":"companyos/runtime/venture_liveness_runtime.py",
    "venture_identity_progression":"companyos/governance/venture_identity_progression.py",
    "connector_engine":"companyos/connectors_live/engine.py",
    "hosting_connector":"companyos/connectors_live/hosting.py",
    "treasury_or_finance":None,
    "dashboard":None,
}
for name,rel in capability_paths.items():
    if rel:
        audit["capabilities"][name]={"present":(ROOT/rel).exists(),"path":rel}
    else:
        if name=="treasury_or_finance":
            matches=[x for x in tracked if re.search(r"(treasury|finance|wallet|transaction)",x,re.I)]
        else:
            matches=[x for x in tracked if re.search(r"(dashboard|web_ui|command_center)",x,re.I)]
        audit["capabilities"][name]={"present":bool(matches),"matching_files":matches[:30]}

# ---------- finance policy conflict scan ----------
# This does NOT expose keys/wallets. It only reports numeric limits found in source/config.
patterns={
    "daily_usd":re.compile(r"(?i)(?:daily[_ ](?:total[_ ]?)?(?:cap|limit)[_ ]?(?:usd)?)[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)"),
    "single_usd":re.compile(r"(?i)(?:single[_ ](?:transaction[_ ]?)?(?:cap|limit)[_ ]?(?:usd)?)[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)"),
    "daily_sol":re.compile(r"(?i)(?:daily[_ ]cap[_ ]sol)[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)"),
    "single_sol":re.compile(r"(?i)(?:single[_ ]cap[_ ]sol)[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?)"),
}
limit_hits=defaultdict(list)
for rel in tracked:
    p=ROOT/rel
    if p.suffix.lower() not in {".py",".sh",".json",".toml",".yaml",".yml",".md"}: continue
    try:
        if p.stat().st_size>1_500_000: continue
        txt=p.read_text(errors="ignore")
    except Exception: continue
    for kind,rx in patterns.items():
        for m in rx.finditer(txt):
            value=m.group(1)
            item={"file":rel,"value":value}
            if item not in limit_hits[kind]:
                limit_hits[kind].append(item)
audit["finance_policy_scan"]["limit_definitions"]={k:v[:100] for k,v in limit_hits.items()}
for kind,rows in limit_hits.items():
    values=sorted({x["value"] for x in rows})
    if len(values)>1:
        audit["warnings"].append(f"multiple_{kind}_values_detected:{','.join(values)}")

# ---------- security: tracked sensitive filenames and secret-like literals ----------
danger_name=re.compile(
    r"(^|/)(?:\.env(?:\.|$)|id_rsa(?:\.pub)?$|credentials?(?:\.json)?$|secrets?(?:\.json)?$|"
    r"wallet(?:_keypair)?(?:\.json)?$|.*private.*\.(?:pem|key|json)$)",
    re.I,
)
allowed_name=re.compile(r"(?:example|sample|template|fixture|test)",re.I)
danger_files=[x for x in tracked if danger_name.search(x) and not allowed_name.search(x)]
audit["security"]["tracked_sensitive_filename_count"]=len(danger_files)
audit["security"]["tracked_sensitive_filenames"]=danger_files[:100]
if danger_files:
    audit["failures"].append("tracked_sensitive_filenames_present")

secret_kinds=Counter()
secret_locs=[]
secret_rx=[
    ("OPENAI_KEY",re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("GITHUB_TOKEN",re.compile(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}")),
    ("PRIVATE_KEY_BLOCK",re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]
for rel in tracked:
    p=ROOT/rel
    try:
        if not p.is_file() or p.stat().st_size>2_000_000: continue
        txt=p.read_text(errors="ignore")
    except Exception: continue
    for n,line in enumerate(txt.splitlines(),1):
        for kind,rx in secret_rx:
            if rx.search(line):
                low=line.lower()
                if any(x in low for x in ("example","placeholder","changeme","dummy","your_key")):
                    continue
                secret_kinds[kind]+=1
                secret_locs.append({"file":rel,"line":n,"type":kind})
audit["security"]["secret_like_literal_counts"]=dict(secret_kinds)
audit["security"]["secret_like_locations"]=secret_locs[:100]
if secret_locs:
    audit["failures"].append("secret_like_literals_present_in_tracked_files")

# ---------- status synthesis ----------
hard_checks=("python_compileall","pytest_full","shell_syntax_all")
for name in hard_checks:
    rec=audit["checks"].get(name,{})
    if rec.get("passed") is False:
        audit["failures"].append(f"check_failed:{name}")

# Native checks are warnings when present but failing; historical stacks may have optional pieces.
for name,rec in audit["checks"].items():
    if name.startswith("native_") and rec.get("passed") is False:
        audit["warnings"].append(f"native_check_failed:{name}")

q=audit["runtime"].get("task_queue") or {}
if isinstance(q,dict) and int(q.get("failed") or 0)>0:
    audit["warnings"].append(f"runtime_failed_tasks:{q.get('failed')}")

if audit["inventory"]["git_status_porcelain"]:
    audit["warnings"].append("worktree_changed_during_audit")

if audit["failures"]:
    overall="FAIL"
elif audit["warnings"]:
    overall="PASS_WITH_WARNINGS"
else:
    overall="PASS"
audit["overall_status"]=overall
audit["failure_count"]=len(audit["failures"])
audit["warning_count"]=len(audit["warnings"])

# JSON report
REPORT_JSON.write_text(json.dumps(audit,indent=2,sort_keys=True,default=str)+"\n")

# Markdown report
inv=audit["inventory"]; rt=audit["runtime"]
lines=[
    "# CompanyOS Full Total Audit",
    "",
    f"- **Status:** {overall}",
    f"- **Repository:** FREEDOMVIKING/CompanyOS",
    f"- **Branch:** `{BRANCH}`",
    f"- **Source snapshot:** `{SOURCE_SHA}`",
    f"- **Tracked files:** {inv.get('tracked_files')}",
    f"- **Python files:** {inv.get('python_files')}",
    f"- **Shell files:** {inv.get('shell_files')}",
    f"- **Tests:** {inv.get('test_files')}",
    f"- **Scripts:** {inv.get('script_files')}",
    f"- **Patch-history scripts:** {inv.get('patch_history_files')}",
    f"- **Commits on branch:** {inv.get('commit_count')}",
    "",
    "## Source integrity",
    "",
]
for name in ("python_compileall","shell_syntax_all","pytest_full"):
    rec=audit["checks"].get(name,{})
    lines.append(f"- **{name}:** {'PASS' if rec.get('passed') is True else 'FAIL' if rec.get('passed') is False else 'SKIPPED'}")
lines += ["","## Runtime inventory",""]
qs=rt.get("task_queue") or {}
lines.append(f"- Task records: {qs.get('total_records','unknown')}")
lines.append(f"- Task states: `{json.dumps(qs.get('states',{}),sort_keys=True)}`")
vs=rt.get("ventures") or {}
lines.append(f"- Canonical ventures: {vs.get('canonical_candidate_count','unknown')}")
lines.append(f"- Venture stages: `{json.dumps(vs.get('stages',{}),sort_keys=True)}`")
lines.append(f"- CompanyOS processes observed: {rt.get('companyos_process_count','unknown')}")
lines += ["","## Capability presence",""]
for k,v in sorted(audit["capabilities"].items()):
    lines.append(f"- {k}: {'PRESENT' if v.get('present') else 'NOT FOUND'}")
lines += ["","## Security",""]
lines.append(f"- Tracked sensitive filenames: {audit['security'].get('tracked_sensitive_filename_count',0)}")
lines.append(f"- Secret-like tracked literals: {sum(audit['security'].get('secret_like_literal_counts',{}).values())}")
lines += ["","## Financial-policy scan",""]
for k,rows in sorted((audit["finance_policy_scan"].get("limit_definitions") or {}).items()):
    vals=sorted({x["value"] for x in rows})
    lines.append(f"- {k}: values found `{', '.join(vals) if vals else 'none'}`")
lines += ["","## Latest version markers observed",""]
lines.append(", ".join(inv.get("latest_version_markers") or []) or "None found")
lines += ["","## Warnings",""]
lines += [f"- {x}" for x in audit["warnings"]] or ["- None"]
lines += ["","## Failures",""]
lines += [f"- {x}" for x in audit["failures"]] or ["- None"]
lines += [
    "",
    "## Audit safety",
    "",
    "- No email/customer outreach was sent by this audit.",
    "- No financial transaction was performed by this audit.",
    "- No deployment or purchase was performed by this audit.",
    "- Detailed command logs remain local under `~/.companyos_runtime/audit_logs/` and are not committed.",
]
REPORT_MD.write_text("\n".join(lines)+"\n")

print(json.dumps({
    "overall_status":overall,
    "tracked_files":inv.get("tracked_files"),
    "python_files":inv.get("python_files"),
    "shell_files":inv.get("shell_files"),
    "tests":inv.get("test_files"),
    "patch_history_files":inv.get("patch_history_files"),
    "task_states":qs.get("states",{}),
    "venture_stages":vs.get("stages",{}),
    "companyos_process_count":rt.get("companyos_process_count"),
    "latest_version_markers":inv.get("latest_version_markers",[])[:10],
    "warnings":audit["warnings"],
    "failures":audit["failures"],
    "report_json":str(REPORT_JSON),
    "report_md":str(REPORT_MD),
},indent=2,sort_keys=True))
PY
AUDIT_RC=$?

# ------------------------------------------------------------
# 7) Commit the audit reports and push again.
# ------------------------------------------------------------
say "===== COMMIT AUDIT REPORTS ====="
git add -- "$REPORT_JSON" "$REPORT_MD" "scripts/companyos_full_sync_audit.sh" "ops/patch_history" 2>/dev/null || true

# Re-run secret gate on audit commit payload.
python - <<'PY'
from pathlib import Path
import subprocess,re,sys
root=Path.home()/"companyos"
files=subprocess.run(
    ["git","diff","--cached","--name-only","--diff-filter=ACMR"],
    cwd=root,text=True,capture_output=True
).stdout.splitlines()
rxs=[
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
hits=[]
for rel in files:
    p=root/rel
    try:
        if not p.is_file() or p.stat().st_size>3_000_000: continue
        txt=p.read_text(errors="ignore")
    except Exception: continue
    for n,line in enumerate(txt.splitlines(),1):
        if any(rx.search(line) for rx in rxs):
            if any(x in line.lower() for x in ("example","placeholder","dummy","changeme")):
                continue
            hits.append((rel,n))
if hits:
    print("AUDIT_REPORT_SECRET_GATE=BLOCK")
    for rel,n in hits[:50]:
        print(f"SECRET_RISK_FILE={rel} LINE={n}")
    sys.exit(42)
print("AUDIT_REPORT_SECRET_GATE=PASS")
PY
REPORT_SECRET_RC=$?
if [ "$REPORT_SECRET_RC" -ne 0 ]; then
  say "AUDIT_REPORT_PUSH_SKIPPED=SECRET_GATE_BLOCKED"
  exit "$REPORT_SECRET_RC"
fi

if ! git diff --cached --quiet; then
  git commit -m "Add comprehensive CompanyOS audit snapshot" || die "audit_commit_failed"
fi

FINAL_SHA="$(git rev-parse HEAD)"
git push origin "HEAD:$BRANCH" || die "audit_push_failed"
REMOTE_FINAL_SHA="$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}' | head -1)"
[ "$REMOTE_FINAL_SHA" = "$FINAL_SHA" ] || die "remote_sha_mismatch_after_audit_push"

say ""
say "===== FINAL SUMMARY ====="
say "GITHUB_PUSH=PASS"
say "AUDIT_PUSH=PASS"
say "BRANCH=$BRANCH"
say "SOURCE_SNAPSHOT_SHA=$SOURCE_SHA"
say "FINAL_SHA=$FINAL_SHA"
say "REMOTE_FINAL_SHA=$REMOTE_FINAL_SHA"
say "REPORT_JSON=$REPORT_JSON"
say "REPORT_MD=$REPORT_MD"

python - <<PY
import json
from pathlib import Path
p=Path("$REPORT_JSON")
try:
    d=json.loads(p.read_text())
    print("AUDIT_STATUS="+str(d.get("overall_status")))
    print("AUDIT_WARNINGS="+str(d.get("warning_count")))
    print("AUDIT_FAILURES="+str(d.get("failure_count")))
    inv=d.get("inventory") or {}
    rt=d.get("runtime") or {}
    print("TRACKED_FILES="+str(inv.get("tracked_files")))
    print("PYTHON_FILES="+str(inv.get("python_files")))
    print("SHELL_FILES="+str(inv.get("shell_files")))
    print("TEST_FILES="+str(inv.get("test_files")))
    print("TASK_STATES="+json.dumps((rt.get("task_queue") or {}).get("states") or {},sort_keys=True))
    print("VENTURE_STAGES="+json.dumps((rt.get("ventures") or {}).get("stages") or {},sort_keys=True))
except Exception as exc:
    print("AUDIT_SUMMARY_READ_ERROR="+type(exc).__name__)
PY

say "COMPANYOS_FULL_GITHUB_SYNC_AND_TOTAL_AUDIT=COMPLETE"
exit "$AUDIT_RC"
