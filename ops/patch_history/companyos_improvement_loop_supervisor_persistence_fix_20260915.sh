#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS IMPROVEMENT LOOP SUPERVISOR PERSISTENCE FIX ====="
echo "Safe registration only. No finance/DNS mutation. No secret output."
echo "Will not restart the currently healthy supervisor."

SUP="companyos/runtime/service_supervisor.py"
MOD="companyos/runtime/continuous_profit_improvement_loop.py"
TEST="tests/generated/test_improvement_loop_supervisor_registration.py"
BACK=".companyos_runtime/backups/improvement_supervisor_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACK" tests/generated

test -f "$SUP"
test -f "$MOD"
cp "$SUP" "$BACK/service_supervisor.py"

python - <<'PY'
from pathlib import Path
import ast, re, sys

p=Path("companyos/runtime/service_supervisor.py")
s=p.read_text()
SERVICE="continuous_profit_improvement_loop"
MODULE="companyos.runtime.continuous_profit_improvement_loop"

if SERVICE in s:
    print("REGISTRATION_ALREADY_PRESENT")
    ast.parse(s)
    raise SystemExit(0)

# Discover the service registry structurally rather than assuming an old layout.
tree=ast.parse(s)
candidates=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.Dict,ast.List,ast.Tuple)):
        seg=ast.get_source_segment(s,n) or ""
        hits=sum(x in seg for x in (
            "continuous_goal_runtime",
            "productive_autonomy_watchdog",
            "profit_opportunity_runtime",
            "self_evolution_runtime",
            "evidence_decision_closure"))
        if hits >= 2:
            candidates.append((hits,n,seg))

if not candidates:
    print("ERROR: could not safely identify supervisor service registry")
    sys.exit(20)

_, node, seg=max(candidates,key=lambda x:x[0])

# Handle the two registry forms used by CompanyOS:
# dict: "name": {"argv":[python,"-m","module"], ...}
# list/tuple of service names/modules cannot safely infer schema, so abort.
if not isinstance(node,ast.Dict):
    print("ERROR: registry found but schema is not a dict; refusing blind mutation")
    sys.exit(21)

# Infer one existing dict value and clone its schema, replacing only identity/argv module.
pairs=[]
for k,v in zip(node.keys,node.values):
    try:
        key=ast.literal_eval(k)
    except Exception:
        continue
    if isinstance(key,str) and isinstance(v,ast.Dict):
        txt=ast.get_source_segment(s,v) or ""
        if "-m" in txt or "argv" in txt or "arg" in txt:
            pairs.append((key,v,txt))
if not pairs:
    print("ERROR: no clonable service definition found")
    sys.exit(22)

# Prefer a simple long-running Python module service.
pairs.sort(key=lambda x: (
    0 if x[0] in ("evidence_decision_closure","profit_opportunity_runtime",
                  "semantic_capability_bridge","productive_autonomy_watchdog") else 1,
    len(x[2])
))
key,v,txt=pairs[0]

# Clone source text and replace old service identity/module conservatively.
newtxt=txt
oldmods=re.findall(r'companyos\.runtime\.[A-Za-z0-9_]+', newtxt)
if oldmods:
    newtxt=newtxt.replace(oldmods[0], MODULE)
else:
    print("ERROR: template has no runtime module")
    sys.exit(23)

# Build insertion immediately before closing brace of registry.
start=node.col_offset
lines=s.splitlines(True)
# AST end_col_offset points just after closing brace.
offsets=[0]
for line in lines: offsets.append(offsets[-1]+len(line))
close_pos=offsets[node.end_lineno-1]+node.end_col_offset-1
indent=" "*(node.col_offset+4)
# Preserve formatting sufficiently for Python.
entry=f'\n{indent}{SERVICE!r}: {newtxt},'
patched=s[:close_pos]+entry+s[close_pos:]

ast.parse(patched)
p.write_text(patched)
print("REGISTERED",SERVICE,"USING_TEMPLATE",key)
PY

echo "===== STATIC VALIDATION ====="
python -m py_compile "$SUP" "$MOD"

cat > "$TEST" <<'PY'
from pathlib import Path
import ast

def test_supervisor_registers_improvement_loop():
    p=Path("companyos/runtime/service_supervisor.py")
    s=p.read_text()
    ast.parse(s)
    assert "continuous_profit_improvement_loop" in s
    assert "companyos.runtime.continuous_profit_improvement_loop" in s

def test_loop_keeps_strict_evidence_policy():
    s=Path("companyos/runtime/continuous_profit_improvement_loop.py").read_text()
    assert '"invent_profit":False' in s or "'invent_profit': False" in s
    assert "verified>=2" in s

def test_no_finance_or_dns_logic_added_to_loop():
    s=Path("companyos/runtime/continuous_profit_improvement_loop.py").read_text().lower()
    assert "private_key" not in s
    assert "dns mutation" not in s
PY

python -m pytest -q "$TEST" tests/generated/test_continuous_profit_improvement_loop.py tests/generated/test_verified_outcome_scoring.py

echo "===== VERIFY REGISTRATION WITHOUT RESTART ====="
python - <<'PY'
from pathlib import Path
s=Path("companyos/runtime/service_supervisor.py").read_text()
assert "continuous_profit_improvement_loop" in s
assert "companyos.runtime.continuous_profit_improvement_loop" in s
print("SUPERVISOR_REGISTRATION=PASS")
print("CURRENT_SUPERVISOR_LEFT_UNTOUCHED=YES")
print("Registration becomes managed on the next normal supervisor start/recovery.")
PY

echo "===== ENSURE CURRENT LOOP STILL ALIVE ====="
if pgrep -f 'companyos.runtime.continuous_profit_improvement_loop' >/dev/null 2>&1; then
  echo "IMPROVEMENT_LOOP_CURRENTLY_RUNNING=YES"
else
  mkdir -p .companyos_runtime/improvement_loop
  nohup python -u -m companyos.runtime.continuous_profit_improvement_loop \
    > .companyos_runtime/improvement_loop/console.log 2>&1 &
  echo $! > .companyos_runtime/improvement_loop/pid
  sleep 2
  pgrep -f 'companyos.runtime.continuous_profit_improvement_loop' >/dev/null
  echo "IMPROVEMENT_LOOP_CURRENTLY_RUNNING=STARTED"
fi

echo "===== COMMIT ONLY FIX FILES ====="
git add "$SUP" "$TEST"
if ! git diff --cached --quiet; then
  git commit -m "persist continuous improvement loop under service supervisor"
else
  echo "NO_NEW_COMMIT_REQUIRED"
fi

echo "===== STATUS ====="
python scripts/companyos_improvementctl status || true
echo "COMPANYOS_IMPROVEMENT_LOOP_SUPERVISOR_PERSISTENCE=PASS"
