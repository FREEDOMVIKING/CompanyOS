#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== COMPANYOS POST-LAUNCH REVENUE LOOP LARGE PUSH ====="
echo "Bounded evidence loop. No finance transfer. No DNS mutation. No supervisor restart."
mkdir -p companyos/runtime scripts tests/generated .companyos_runtime

cat > companyos/runtime/post_launch_revenue_loop.py <<'PY'
from __future__ import annotations
import json, os, tempfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p,d=None):
    try:return json.loads(Path(p).read_text())
    except Exception:return {} if d is None else d
def write_json(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class PostLaunchRevenueLoop:
    """Evidence-driven post-launch controller.

    Never invents revenue/conversions. Unknown metrics stay unknown.
    Decisions are bounded to improve/scale/hold/kill recommendations.
    Financial, credential, DNS and irreversible external actions remain outside.
    """
    def __init__(self,root):
        self.root=Path(root); self.rt=self.root/".companyos_runtime"

    def latest_launch(self):
        return read_json(self.rt/"venture_launch_latest.json",{})

    def collect_public_evidence(self,launch):
        url=launch.get("public_url")
        e={"timestamp":now(),"public_url":url,"site_reachable":False,"http_status":None,
           "revenue":None,"leads":None,"conversions":None,"traffic":None,
           "evidence_quality":"availability_only"}
        if not url:return e
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CompanyOS-Evidence/1.0"})
            with urllib.request.urlopen(req,timeout=20) as r:
                e["http_status"]=getattr(r,"status",200)
                e["site_reachable"]=200 <= e["http_status"] < 400
        except Exception as x:
            e["error"]=str(x)[:500]
        return e

    def decide(self,launch,evidence):
        if launch.get("status")!="launched":
            return {"decision":"hold","reason":"no_active_launched_venture","confidence":1.0}
        if not evidence.get("site_reachable"):
            return {"decision":"improve","reason":"public_site_unreachable","confidence":0.95,
                    "next_action":"diagnose_and_restore_public_site"}
        revenue=evidence.get("revenue"); conversions=evidence.get("conversions")
        if isinstance(revenue,(int,float)) and revenue > 0:
            return {"decision":"scale","reason":"observed_positive_revenue","confidence":0.9,
                    "next_action":"increase_validated_distribution_within_existing_gates"}
        if isinstance(conversions,(int,float)) and conversions > 0:
            return {"decision":"improve","reason":"observed_conversion_without_revenue_evidence","confidence":0.8,
                    "next_action":"improve_offer_and_revenue_capture"}
        return {"decision":"hold","reason":"insufficient_market_evidence","confidence":0.9,
                "next_action":"acquire_real_traffic_lead_conversion_and_revenue_evidence"}

    def run(self):
        launch=self.latest_launch()
        evidence=self.collect_public_evidence(launch)
        decision=self.decide(launch,evidence)
        record={"timestamp":now(),"venture":launch.get("title"),"opportunity_id":launch.get("opportunity_id"),
                "public_url":launch.get("public_url"),"evidence":evidence,**decision}
        write_json(self.rt/"post_launch_revenue_latest.json",record)
        with (self.rt/"post_launch_revenue_ledger.jsonl").open("a") as f:f.write(json.dumps(record,sort_keys=True)+"\n")
        request={"timestamp":now(),"source":"post_launch_revenue_loop","opportunity_id":record.get("opportunity_id"),
                 "decision":record["decision"],"reason":record["reason"],"next_action":record.get("next_action"),
                 "public_url":record.get("public_url"),"requires_real_evidence":True}
        write_json(self.rt/"post_launch_next_action.json",request)
        with (self.rt/"outcome_evidence_queue.jsonl").open("a") as f:f.write(json.dumps({"kind":"post_launch_evidence",**record},sort_keys=True)+"\n")
        return record
PY

cat > companyos/runtime/venture_performance_feedback.py <<'PY'
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
def now():return datetime.now(timezone.utc).isoformat()
class VenturePerformanceFeedback:
    def __init__(self,root):self.root=Path(root);self.rt=self.root/".companyos_runtime"
    def run(self):
        p=self.rt/"post_launch_revenue_latest.json"
        if not p.exists():return {"status":"waiting","reason":"no_post_launch_result"}
        r=json.loads(p.read_text())
        signal={"timestamp":now(),"source":"venture_performance_feedback",
                "opportunity_id":r.get("opportunity_id"),"decision":r.get("decision"),
                "confidence":r.get("confidence"),"reason":r.get("reason"),
                "next_action":r.get("next_action"),"observed_revenue":r.get("evidence",{}).get("revenue"),
                "observed_conversions":r.get("evidence",{}).get("conversions")}
        q=self.rt/"profit_feedback_queue.jsonl"
        with q.open("a") as f:f.write(json.dumps(signal,sort_keys=True)+"\n")
        (self.rt/"venture_performance_feedback.json").write_text(json.dumps(signal,indent=2,sort_keys=True))
        return {"status":"queued","signal":signal}
PY

cat > scripts/companyos_revenueloop <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.post_launch_revenue_loop import PostLaunchRevenueLoop
from companyos.runtime.venture_performance_feedback import VenturePerformanceFeedback
r=PostLaunchRevenueLoop(ROOT).run(); f=VenturePerformanceFeedback(ROOT).run()
print(json.dumps({"revenue_loop":r,"feedback":f},indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_revenueloop

cat > scripts/companyos_revenuestatus <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import json
from pathlib import Path
rt=Path.cwd()/".companyos_runtime"
def x(n):
    try:return json.loads((rt/n).read_text())
    except:return None
print(json.dumps({"latest":x("post_launch_revenue_latest.json"),
"next_action":x("post_launch_next_action.json"),
"performance_feedback":x("venture_performance_feedback.json")},indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_revenuestatus

cat > tests/generated/test_post_launch_revenue_loop.py <<'PY'
from companyos.runtime.post_launch_revenue_loop import PostLaunchRevenueLoop
def test_no_fake_metrics(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    e=r.collect_public_evidence({})
    assert e["revenue"] is None and e["leads"] is None and e["conversions"] is None and e["traffic"] is None
def test_unreachable_improves(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    d=r.decide({"status":"launched"},{"site_reachable":False})
    assert d["decision"]=="improve"
def test_unknown_market_data_holds(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    d=r.decide({"status":"launched"},{"site_reachable":True,"revenue":None,"conversions":None})
    assert d["decision"]=="hold" and "evidence" in d["reason"]
def test_observed_revenue_scales(tmp_path):
    r=PostLaunchRevenueLoop(tmp_path)
    d=r.decide({"status":"launched"},{"site_reachable":True,"revenue":25,"conversions":1})
    assert d["decision"]=="scale"
PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/post_launch_revenue_loop.py companyos/runtime/venture_performance_feedback.py scripts/companyos_revenueloop
echo "===== TEST FULL LAUNCH + REVENUE LAYER ====="
python -m pytest -q tests/generated/test_cloudflare_hosting.py tests/generated/test_website_deployer_cloudflare.py tests/generated/test_venture_launch_orchestrator.py tests/generated/test_post_launch_revenue_loop.py

echo "===== REAL PUBLIC EVIDENCE RUN ====="
python scripts/companyos_revenueloop | tee .companyos_runtime/post_launch_revenue_commissioning.json
echo "===== STATUS ====="
python scripts/companyos_revenuestatus

echo "===== ASSERT NO INVENTED BUSINESS METRICS ====="
python - <<'PY'
import json
from pathlib import Path
r=json.loads(Path(".companyos_runtime/post_launch_revenue_latest.json").read_text())
e=r["evidence"]
assert e["revenue"] is None and e["leads"] is None and e["conversions"] is None and e["traffic"] is None
assert r["decision"] in {"hold","improve","scale","kill"}
print("EVIDENCE_INTEGRITY=PASS")
print("DECISION="+r["decision"])
print("NEXT_ACTION="+str(r.get("next_action")))
PY

echo "===== COMMIT ONLY THIS REVENUE PUSH ====="
git add companyos/runtime/post_launch_revenue_loop.py companyos/runtime/venture_performance_feedback.py scripts/companyos_revenueloop scripts/companyos_revenuestatus tests/generated/test_post_launch_revenue_loop.py
git commit -m "add evidence driven post launch revenue feedback loop" || true

echo "===== SUPERVISOR UNTOUCHED ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if p.exists():
 r=json.loads(p.read_text());print("running:",r.get("running"));print("supervisor_alive:",r.get("supervisor_alive"));print("stop_requested:",r.get("stop_requested"))
else:print("state unavailable; no restart attempted")
PY
echo "===== FINAL ====="
git rev-parse --short HEAD
git status --short
echo "COMPANYOS_POST_LAUNCH_REVENUE_LOOP=PASS"
