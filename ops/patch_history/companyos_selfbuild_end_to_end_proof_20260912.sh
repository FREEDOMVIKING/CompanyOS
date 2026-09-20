#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="${COMPANYOS_HOME:-$HOME/companyos}"
ENV_FILE="$HOME/.companyos_launch_env"
STAMP="$(date +%Y%m%d_%H%M%S)"
PROOF_DIR="$ROOT/.companyos_runtime/self_evolution/proofs/$STAMP"
mkdir -p "$PROOF_DIR"

cd "$ROOT"
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE missing"; exit 1; }
source "$ENV_FILE"

echo "============================================================"
echo " CompanyOS END-TO-END SELF-BUILD PROOF"
echo "============================================================"

echo "[1/9] Capture pre-test state..."
git rev-parse HEAD > "$PROOF_DIR/head_before.txt"
git status --porcelain=v1 > "$PROOF_DIR/dirty_before.txt"

echo "[2/9] Baseline full test discovery..."
set +e
python -m unittest discover -s tests -p 'test*.py' >"$PROOF_DIR/tests_before.out" 2>"$PROOF_DIR/tests_before.err"
BASE_RC=$?
set -e
echo "$BASE_RC" > "$PROOF_DIR/tests_before.rc"

python - <<'PY' "$PROOF_DIR"
import json,re,sys
from pathlib import Path
p=Path(sys.argv[1])
text=(p/"tests_before.out").read_text(errors="replace")+"\n"+(p/"tests_before.err").read_text(errors="replace")
rc=int((p/"tests_before.rc").read_text().strip())
failures=errors=0
m=re.search(r'FAILED\s*\(([^)]*)\)',text)
if m:
    for part in m.group(1).split(","):
        if "=" not in part: continue
        k,v=[x.strip() for x in part.split("=",1)]
        try:v=int(v)
        except:continue
        if k=="failures": failures=v
        elif k=="errors": errors=v
ran=None
m=re.search(r'Ran\s+(\d+)\s+tests?',text)
if m: ran=int(m.group(1))
obj={"returncode":rc,"failures":failures,"errors":errors,"ran":ran,"regression_score":failures+errors}
(p/"baseline_summary.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
print("BASELINE_TESTS="+json.dumps(obj,sort_keys=True))
PY

echo "[3/9] Run one guarded evolution cycle..."
export COMPANYOS_SELF_EVOLUTION_FULL_TESTS=0
set +e
scripts/companyos_evolutionctl once >"$PROOF_DIR/cycle.out" 2>"$PROOF_DIR/cycle.err"
CYCLE_RC=$?
set -e
echo "$CYCLE_RC" > "$PROOF_DIR/cycle.rc"
tail -160 "$PROOF_DIR/cycle.out"
[ -s "$PROOF_DIR/cycle.err" ] && { echo "--- cycle stderr ---"; tail -80 "$PROOF_DIR/cycle.err"; }

git rev-parse HEAD > "$PROOF_DIR/head_after_cycle.txt"
git status --porcelain=v1 > "$PROOF_DIR/dirty_after_cycle.txt"

HEAD_BEFORE="$(cat "$PROOF_DIR/head_before.txt")"
HEAD_AFTER="$(cat "$PROOF_DIR/head_after_cycle.txt")"

echo "HEAD_BEFORE=$HEAD_BEFORE"
echo "HEAD_AFTER=$HEAD_AFTER"

if [ "$HEAD_BEFORE" = "$HEAD_AFTER" ]; then
  echo "PROMOTION_DETECTED=false"
  echo "SELF_BUILD_PROOF=NO_PROMOTION"
  echo "Proof artifacts: $PROOF_DIR"
  exit 2
fi

echo "PROMOTION_DETECTED=true"

echo "[4/9] Verify promotion commit ownership..."
PROMOTE_MSG="$(git log -1 --pretty=%s)"
echo "PROMOTION_COMMIT_MESSAGE=$PROMOTE_MSG"
case "$PROMOTE_MSG" in
  *"self-evolution"*|*"Self-evolution"*|*"Promote self-evolution candidate"*) ;;
  *)
    echo "ERROR: latest commit is not recognized as self-evolution promotion."
    exit 3
    ;;
esac

echo "[5/9] Post-promotion full regression test..."
set +e
python -m unittest discover -s tests -p 'test*.py' >"$PROOF_DIR/tests_after.out" 2>"$PROOF_DIR/tests_after.err"
POST_RC=$?
set -e
echo "$POST_RC" > "$PROOF_DIR/tests_after.rc"

set +e
python - <<'PY' "$PROOF_DIR"
import json,re,sys
from pathlib import Path
p=Path(sys.argv[1])
def parse(outf,errf,rcf):
    text=outf.read_text(errors="replace")+"\n"+errf.read_text(errors="replace")
    rc=int(rcf.read_text().strip())
    failures=errors=0
    m=re.search(r'FAILED\s*\(([^)]*)\)',text)
    if m:
        for part in m.group(1).split(","):
            if "=" not in part: continue
            k,v=[x.strip() for x in part.split("=",1)]
            try:v=int(v)
            except:continue
            if k=="failures": failures=v
            elif k=="errors": errors=v
    ran=None
    m=re.search(r'Ran\s+(\d+)\s+tests?',text)
    if m: ran=int(m.group(1))
    return {"returncode":rc,"failures":failures,"errors":errors,"ran":ran,"regression_score":failures+errors}
before=json.loads((p/"baseline_summary.json").read_text())
after=parse(p/"tests_after.out",p/"tests_after.err",p/"tests_after.rc")
result={"before":before,"after":after,"regressed":after["regression_score"]>before["regression_score"],"improved":after["regression_score"]<before["regression_score"]}
(p/"regression_comparison.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print("REGRESSION_COMPARISON="+json.dumps(result,sort_keys=True))
raise SystemExit(9 if result["regressed"] else 0)
PY
COMPARE_RC=$?
set -e

if [ "$COMPARE_RC" = "9" ]; then
  echo "REGRESSION_DETECTED=true"
  git revert --no-edit "$HEAD_AFTER" || { git revert --abort || true; echo "ROLLBACK=FAILED"; exit 10; }
  [ -x scripts/companyosctl ] && scripts/companyosctl restart || true
  sleep 6
  echo "ROLLBACK=PASS"
  echo "SELF_BUILD_PROOF=FAILED_REGRESSION_ROLLED_BACK"
  exit 11
fi

echo "REGRESSION_DETECTED=false"

echo "[6/9] Verify dirty-file preservation..."
set +e
python - <<'PY' "$PROOF_DIR"
import sys
from pathlib import Path
p=Path(sys.argv[1])
def paths(file):
    out=[]
    for raw in file.read_text(errors="replace").splitlines():
        if len(raw)<4: continue
        path=raw[3:]
        if " -> " in path: path=path.split(" -> ",1)[1]
        out.append(path.strip())
    return sorted(set(out))
before=paths(p/"dirty_before.txt")
after=paths(p/"dirty_after_cycle.txt")
added=sorted(set(after)-set(before))
removed=sorted(set(before)-set(after))
print("DIRTY_BEFORE_COUNT="+str(len(before)))
print("DIRTY_AFTER_COUNT="+str(len(after)))
print("DIRTY_ADDED="+repr(added))
print("DIRTY_REMOVED="+repr(removed))
raise SystemExit(12 if added or removed else 0)
PY
DIRTY_RC=$?
set -e

if [ "$DIRTY_RC" = "12" ]; then
  echo "ERROR: uncommitted working tree changed; reverting promotion."
  git revert --no-edit "$HEAD_AFTER" || true
  [ -x scripts/companyosctl ] && scripts/companyosctl restart || true
  exit 12
fi
echo "DIRTY_WORKTREE_PRESERVED=PASS"

echo "[7/9] Restart and verify all five services..."
[ -x scripts/companyosctl ] && scripts/companyosctl restart || true
sleep 8

python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/".companyos_runtime"/"service_supervisor_state.json"
expected={"continuous_goal_runtime","local_dashboard","productive_autonomy_watchdog","profit_opportunity_runtime","self_evolution_runtime"}
d=json.loads(p.read_text()) if p.exists() else {}
services=d.get("services") or {}
bad=[]
for name in sorted(expected):
    row=services.get(name) or {}
    running=bool(row.get("running"))
    failures=int(row.get("consecutive_failures") or 0)
    print(f"{name}: running={running} failures={failures}")
    if not running or failures: bad.append(name)
if bad: raise SystemExit("UNHEALTHY_SERVICES="+",".join(bad))
print("ALL_5_SERVICES_HEALTHY=PASS")
PY

echo "[8/9] Dashboard health..."
HEALTH_FILE="$PROOF_DIR/dashboard_health.json"
curl -fsS http://127.0.0.1:8765/api/health > "$HEALTH_FILE"
python - <<'PY' "$HEALTH_FILE"
import json,sys
d=json.load(open(sys.argv[1]))
print("DASHBOARD_HEALTHY="+str(bool(d.get("healthy"))).lower())
print("CORE_EXTERNAL_READY="+str(bool(d.get("core_external_ready"))).lower())
if not d.get("healthy"): raise SystemExit(1)
PY

echo "[9/9] Push accepted autonomous promotion..."
BRANCH="$(git branch --show-current)"
[ -n "$BRANCH" ] && git push origin "$BRANCH" || true
git log -3 --oneline | tee "$PROOF_DIR/final_git_log.txt"

echo
echo "SELF-BUILD END-TO-END PROOF = PASS"
echo "Proof artifacts: $PROOF_DIR"
echo "Promoted commit: $HEAD_AFTER"
echo "Existing dirty working tree preserved."
echo "No test regression versus pre-cycle baseline."
echo "All five services healthy after restart."
echo "COMPANYOS_SELFBUILD_END_TO_END_PROOF=PASS"
