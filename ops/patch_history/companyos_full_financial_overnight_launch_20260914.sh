#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== COMPANYOS FULL OVERNIGHT PRODUCTION LAUNCH ====="
echo "Live finance enabled with HARD AGGREGATE USD 50.00 outbound cap."
echo "Inbound receipts are not capped. Existing approval/security gates remain enforced."

mkdir -p .companyos_runtime/overnight companyos/runtime scripts tests/generated
chmod 700 .companyos_runtime/overnight

cat > companyos/runtime/overnight_finance_guard.py <<'PY'
from __future__ import annotations
import fcntl,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

CAP=50.0
def now():return datetime.now(timezone.utc).isoformat()
class OvernightFinanceGuard:
    """Atomic aggregate outbound budget guard. Receiving is not charged."""
    def __init__(self,root):
        self.root=Path(root);self.d=self.root/".companyos_runtime/overnight"
        self.d.mkdir(parents=True,exist_ok=True);self.state=self.d/"finance_budget.json";self.lock=self.d/"finance_budget.lock"
        if not self.state.exists():self._write({"cap_usd":CAP,"spent_usd":0.0,"reserved_usd":0.0,"started_at":now(),"mode":"overnight"})
    def _read(self):
        try:return json.loads(self.state.read_text())
        except:return {"cap_usd":CAP,"spent_usd":0.0,"reserved_usd":0.0}
    def _write(self,d):
        fd,t=tempfile.mkstemp(dir=str(self.d),prefix="budget.")
        with os.fdopen(fd,"w") as f:json.dump(d,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(t,self.state)
    def reserve(self,usd,tx_id):
        usd=float(usd)
        if usd < 0:return {"allowed":False,"reason":"negative_amount"}
        with self.lock.open("a+") as lk:
            fcntl.flock(lk,fcntl.LOCK_EX);s=self._read()
            remaining=s["cap_usd"]-s["spent_usd"]-s["reserved_usd"]
            if usd > remaining+1e-9:return {"allowed":False,"reason":"overnight_cap_exceeded","remaining_usd":round(remaining,2)}
            s["reserved_usd"]=round(s["reserved_usd"]+usd,8);self._write(s)
            self._ledger({"kind":"reserve","tx_id":tx_id,"usd":usd,"timestamp":now()})
            return {"allowed":True,"remaining_after_reservation_usd":round(remaining-usd,2)}
    def settle(self,usd,tx_id,success):
        usd=float(usd)
        with self.lock.open("a+") as lk:
            fcntl.flock(lk,fcntl.LOCK_EX);s=self._read()
            s["reserved_usd"]=max(0,round(s["reserved_usd"]-usd,8))
            if success:s["spent_usd"]=round(s["spent_usd"]+usd,8)
            self._write(s);self._ledger({"kind":"settle","tx_id":tx_id,"usd":usd,"success":bool(success),"timestamp":now()})
            return s
    def receive(self,amount,asset,ref=None):
        # No inbound ceiling; this records evidence only and never signs a transfer.
        x={"kind":"receive","amount":amount,"asset":asset,"ref":ref,"timestamp":now()}
        self._ledger(x);return {"accepted":True,"counts_against_outbound_cap":False}
    def status(self):
        s=self._read();s["remaining_usd"]=round(s["cap_usd"]-s["spent_usd"]-s["reserved_usd"],2);return s
    def _ledger(self,x):
        with (self.d/"finance_ledger.jsonl").open("a") as f:f.write(json.dumps(x,sort_keys=True)+"\n")
PY

cat > scripts/companyos_overnight_finance <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.overnight_finance_guard import OvernightFinanceGuard
p=argparse.ArgumentParser();sp=p.add_subparsers(dest="cmd",required=True);sp.add_parser("status")
r=sp.add_parser("reserve");r.add_argument("--usd",type=float,required=True);r.add_argument("--tx-id",required=True)
q=sp.add_parser("settle");q.add_argument("--usd",type=float,required=True);q.add_argument("--tx-id",required=True);q.add_argument("--success",action="store_true")
a=p.parse_args();g=OvernightFinanceGuard(ROOT)
o=g.status() if a.cmd=="status" else g.reserve(a.usd,a.tx_id) if a.cmd=="reserve" else g.settle(a.usd,a.tx_id,a.success)
print(json.dumps(o,indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_overnight_finance

cat > scripts/companyos_overnight_status <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.overnight_finance_guard import OvernightFinanceGuard
def read(p):
 try:return json.loads(p.read_text())
 except:return None
print(json.dumps({
 "finance":OvernightFinanceGuard(ROOT).status(),
 "supervisor":read(ROOT/".companyos_runtime/service_supervisor_state.json"),
 "ceo_workforce":read(ROOT/".companyos_runtime/ceo_workforce/latest.json"),
 "revenue":read(ROOT/".companyos_runtime/post_launch_revenue_latest.json"),
 "market_evidence":read(ROOT/".companyos_runtime/market_evidence_summary.json"),
},indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_overnight_status

cat > tests/generated/test_overnight_finance_guard.py <<'PY'
from companyos.runtime.overnight_finance_guard import OvernightFinanceGuard
def test_aggregate_cap(tmp_path):
 g=OvernightFinanceGuard(tmp_path)
 assert g.reserve(30,"a")["allowed"];g.settle(30,"a",True)
 assert g.reserve(20,"b")["allowed"];g.settle(20,"b",True)
 assert not g.reserve(.01,"c")["allowed"]
 assert g.status()["spent_usd"]==50
def test_parallel_reservations_cannot_exceed_cap(tmp_path):
 import concurrent.futures
 g=OvernightFinanceGuard(tmp_path)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as x:
  rs=list(x.map(lambda i:g.reserve(10,f"t{i}"),range(8)))
 assert sum(bool(r["allowed"]) for r in rs)==5
 assert g.status()["reserved_usd"]==50
def test_failed_transaction_releases_budget(tmp_path):
 g=OvernightFinanceGuard(tmp_path);assert g.reserve(50,"x")["allowed"]
 g.settle(50,"x",False);assert g.status()["remaining_usd"]==50
def test_receiving_not_capped(tmp_path):
 g=OvernightFinanceGuard(tmp_path)
 assert g.receive(1000000,"USDC")["accepted"]
 assert g.status()["remaining_usd"]==50
PY

echo "===== PRE-FLIGHT: SECRETS PRESENT WITHOUT PRINTING THEM ====="
python - <<'PY'
import os,sys
required=["OPENAI_API_KEY","SOLANA_RPC_URL","SOLANA_PRIVATE_KEY","CLOUDFLARE_API_TOKEN","CLOUDFLARE_ACCOUNT_ID"]
missing=[x for x in required if not os.getenv(x)]
print("required_secret_fields:",{x:bool(os.getenv(x)) for x in required})
if missing: print("MISSING:",",".join(missing));sys.exit(2)
print("SECRET_PREFLIGHT=PASS")
PY

echo "===== COMPILE + FINANCE TESTS ====="
python -m py_compile companyos/runtime/overnight_finance_guard.py scripts/companyos_overnight_finance scripts/companyos_overnight_status
python -m pytest -q tests/generated/test_overnight_finance_guard.py tests/generated/test_autonomous_agent_workforce.py tests/generated/test_ceo_workforce_orchestrator.py

echo "===== RESET TONIGHT'S BUDGET TO EXACTLY USD 50 ====="
rm -f .companyos_runtime/overnight/finance_budget.json .companyos_runtime/overnight/finance_budget.lock
python scripts/companyos_overnight_finance status

echo "===== ENABLE LIVE FINANCE FOR THIS SHELL/RUNTIME ====="
export COMPANYOS_ENABLE_LIVE_FINANCE=1
export COMPANYOS_OVERNIGHT_OUTBOUND_CAP_USD=50
export COMPANYOS_OVERNIGHT_FINANCE_GUARD=1
cat > .companyos_runtime/overnight/policy.json <<EOF
{
  "live_finance": true,
  "aggregate_outbound_cap_usd": 50.0,
  "inbound_cap": null,
  "existing_approval_gates_preserved": true,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "===== VERIFY CURRENT SUPERVISOR; DO NOT START DUPLICATE ====="
python - <<'PY'
import json,sys
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if not p.exists():
 print("SUPERVISOR_STATE_MISSING");sys.exit(3)
r=json.loads(p.read_text())
print("running:",r.get("running"))
if r.get("running") is not True:
 print("SUPERVISOR_NOT_CONFIRMED_RUNNING");sys.exit(3)
print("SUPERVISOR_PREFLIGHT=PASS")
PY

echo "===== START OVERNIGHT CEO LOOP ONLY IF NOT ALREADY RUNNING ====="
if [ -f .companyos_runtime/overnight/ceo_loop.pid ] && kill -0 "$(cat .companyos_runtime/overnight/ceo_loop.pid)" 2>/dev/null; then
  echo "CEO_OVERNIGHT_LOOP_ALREADY_RUNNING pid=$(cat .companyos_runtime/overnight/ceo_loop.pid)"
else
  cat > .companyos_runtime/overnight/ceo_loop.sh <<'EOS'
#!/data/data/com.termux/files/usr/bin/bash
set -u
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a
export COMPANYOS_ENABLE_LIVE_FINANCE=1
export COMPANYOS_OVERNIGHT_OUTBOUND_CAP_USD=50
export COMPANYOS_OVERNIGHT_FINANCE_GUARD=1
while :; do
  date -u +"===== CEO CYCLE %Y-%m-%dT%H:%M:%SZ ====="
  python scripts/companyos_ceoworkforce || true
  python scripts/companyos_revenueloop || true
  python scripts/companyos_overnight_status || true
  sleep 900
done
EOS
  chmod +x .companyos_runtime/overnight/ceo_loop.sh
  nohup .companyos_runtime/overnight/ceo_loop.sh >> .companyos_runtime/overnight/ceo_loop.log 2>&1 &
  echo $! > .companyos_runtime/overnight/ceo_loop.pid
  sleep 2
  kill -0 "$(cat .companyos_runtime/overnight/ceo_loop.pid)"
  echo "CEO_OVERNIGHT_LOOP_STARTED pid=$(cat .companyos_runtime/overnight/ceo_loop.pid)"
fi

echo "===== COMMIT GUARD + CONTROLS ONLY ====="
git add companyos/runtime/overnight_finance_guard.py scripts/companyos_overnight_finance scripts/companyos_overnight_status tests/generated/test_overnight_finance_guard.py
git commit -m "add hard aggregate overnight finance budget guard" || true

echo "===== LIVE STATUS ====="
python scripts/companyos_overnight_status
echo
echo "LOCAL_DASHBOARD=http://127.0.0.1:8765"
echo "OVERNIGHT_LOG=$HOME/companyos/.companyos_runtime/overnight/ceo_loop.log"
echo "OVERNIGHT_TOTAL_OUTBOUND_CAP_USD=50.00"
echo "INBOUND_CAP=NONE"
echo "LIVE_FINANCE=ON"
echo "COMPANYOS_FULL_FINANCIAL_OVERNIGHT_LAUNCH=PASS"
