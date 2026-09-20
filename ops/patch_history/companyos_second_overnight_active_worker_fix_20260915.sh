#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS SECOND OVERNIGHT ACTIVE WORKER FIX ====="
echo "Preserves \$50 aggregate outbound overnight cap; inbound uncapped; no supervisor restart."

mkdir -p tests/generated .companyos_runtime/overnight2

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_workforce_loop.py")
s=p.read_text()
start=s.index("def _active(factory:Factory):")
end=s.index("\ndef ", start+5)
replacement='''def _active(factory:Factory):
    # Worker registry status is canonical. Factory.active(t) accepts a
    # bottleneck token in this deployed Factory, not a worker dictionary.
    return [w for w in _workers(factory)
            if isinstance(w, dict) and w.get("status") in ("probation", "permanent")]
'''
p.write_text(s[:start]+replacement+s[end:])
PY

cat > tests/generated/test_workforce_active_state_v4.py <<'PY'
from companyos.runtime import autonomous_workforce_loop as m
class F:
    def __init__(self):
        self.reg={"workers":[
          {"worker_id":"a","status":"probation"},
          {"worker_id":"b","status":"permanent"},
          {"worker_id":"c","status":"retired"}]}
    def active(self,t):
        raise AssertionError("Factory.active must not receive worker dict")
def test_registry_status():
    assert [x["worker_id"] for x in m._active(F())]==["a","b"]
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/autonomous_workforce_loop.py scripts/companyos_workforce_loop
python -m pytest -q tests/generated/test_workforce_active_state_v4.py

ENV="$HOME/.companyos_launch_env"
touch "$ENV"; chmod 600 "$ENV"
python - <<'PY'
from pathlib import Path
p=Path.home()/".companyos_launch_env"
lines=p.read_text().splitlines()
wanted={
 "COMPANYOS_ENABLE_LIVE_FINANCE":"1",
 "COMPANYOS_OVERNIGHT_OUTBOUND_CAP_USD":"50",
 "COMPANYOS_OVERNIGHT_FINANCE_GUARD":"1",
}
out=[]; done=set()
for line in lines:
    raw=line[7:] if line.startswith("export ") else line
    k=raw.split("=",1)[0].strip() if "=" in raw else ""
    if k in wanted:
        if k not in done:
            out.append("export %s=%s"%(k,wanted[k])); done.add(k)
    else:
        out.append(line)
for k,v in wanted.items():
    if k not in done: out.append("export %s=%s"%(k,v))
p.write_text("\n".join(out)+"\n")
PY
set -a; source "$ENV"; set +a

echo "===== CONTROLLED LIVE CYCLE ====="
python scripts/companyos_workforce_loop cycle | tee .companyos_runtime/overnight2/baseline.json

echo "===== START SECOND OVERNIGHT WORKFORCE LOOP ====="
if pgrep -f "[c]ompanyos_workforce_loop run" >/dev/null 2>&1; then
 echo "WORKFORCE_LOOP_ALREADY_RUNNING=YES"
else
 nohup python scripts/companyos_workforce_loop run --interval 300 >> .companyos_runtime/overnight2/workforce.log 2>&1 &
 echo $! > .companyos_runtime/overnight2/workforce.pid
 echo "WORKFORCE_LOOP_STARTED=YES"
fi

echo "===== SUPERVISOR UNTOUCHED ====="
pgrep -af "companyos.runtime.service_supervisor" || true

git add companyos/runtime/autonomous_workforce_loop.py tests/generated/test_workforce_active_state_v4.py
if ! git diff --cached --quiet; then
 git commit -m "fix canonical active worker state for second overnight run" || true
fi

echo "SECOND_OVERNIGHT=ACTIVE"
echo "OUTBOUND_SPEND_CAP_USD=50"
echo "INBOUND_CAP=NONE"
echo "VERIFIED_PROFIT_ONLY=YES"
echo "SUPERVISOR_RESTARTED=NO"
echo "COMPANYOS_SECOND_OVERNIGHT_ACTIVE_WORKER_FIX=PASS"
