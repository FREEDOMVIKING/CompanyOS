#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== VERIFIED OUTCOME SCORING V2 FIX ====="
echo "Keeps strict production threshold; fixes commissioning test to match it."
echo "No finance transfer. No DNS mutation. No supervisor restart."

mkdir -p tests/generated .companyos_runtime/verified_outcomes

cat > tests/generated/test_verified_outcome_scoring.py <<'PY'
from companyos.runtime.verified_outcome_scoring import VerifiedOutcomeScorer

def test_activity_alone_not_permanent(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={
        "role":"candidate_qualification",
        "jobs":3,
        "successes":3,
        "failures":0,
        "status":"permanent",
    }
    r=s.evaluate_worker(w,[])
    assert r["status"]=="probation"
    assert r["verified_outcome_score"]==0

def test_real_outcomes_below_threshold_stay_probation(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={"role":"candidate_qualification","jobs":3,"successes":3,"failures":0}
    sig=[
        {"class":"opportunity_advanced","weight":20,"source":"a"},
        {"class":"verified_evidence","weight":20,"source":"b"},
    ]
    r=s.evaluate_worker(w,sig)
    assert r["verified_outcome_score"]==40
    assert r["verified_score"]==55.0
    assert r["status"]=="probation"

def test_sufficient_real_outcomes_can_promote(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={"role":"candidate_qualification","jobs":3,"successes":3,"failures":0}
    sig=[
        {"class":"opportunity_advanced","weight":20,"source":"a"},
        {"class":"verified_evidence","weight":20,"source":"b"},
        {"class":"verified_evidence","weight":20,"source":"c"},
    ]
    r=s.evaluate_worker(w,sig)
    assert r["verified_outcome_score"]==60
    assert r["verified_score"]==70.0
    assert r["status"]=="permanent"

def test_revenue_role_does_not_use_deployment_as_revenue(tmp_path):
    s=VerifiedOutcomeScorer(tmp_path)
    w={"role":"revenue_evidence","jobs":3,"failures":0}
    sig=[{"class":"deployment_or_reachability","weight":15,"source":"x"}]
    r=s.evaluate_worker(w,sig)
    assert r["verified_outcome_score"]==0
    assert r["status"]=="probation"
PY

echo "===== COMPILE ====="
python -m py_compile \
  companyos/runtime/verified_outcome_scoring.py \
  scripts/companyos_verify_worker_outcomes

echo "===== TEST STRICT POLICY ====="
python -m pytest -q tests/generated/test_verified_outcome_scoring.py

echo "===== LIVE VERIFIED OUTCOME EVALUATION ====="
python scripts/companyos_verify_worker_outcomes \
  | tee .companyos_runtime/verified_outcomes/commissioning_v2.json

echo "===== VERIFY POLICY ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/verified_outcomes/latest.json")
d=json.loads(p.read_text())
assert d["policy"]["file_presence_is_success"] is False
assert d["policy"]["revenue_requires_explicit_observed_marker"] is True
assert d["policy"]["permanence_requires_downstream_outcomes"] is True
print("PERMANENT:", d["permanent"])
print("PROBATION:", d["probation"])
print("RETIRED:", d["retired"])
print("VERIFIED_SIGNALS:", len(d["signals"]))
print("STRICT_OUTCOME_POLICY=PASS")
PY

echo "===== COMMIT ONLY FIX ====="
git add tests/generated/test_verified_outcome_scoring.py
git commit -m "align verified outcome tests with strict promotion threshold" || true

echo "===== SUPERVISOR UNTOUCHED ====="
python - <<'PY'
import json
from pathlib import Path
p=Path(".companyos_runtime/service_supervisor_state.json")
if p.exists():
    d=json.loads(p.read_text())
    print("supervisor_pid:", d.get("supervisor_pid"))
    print("stop_requested:", d.get("stop_requested"))
else:
    print("No supervisor mutation performed.")
PY

echo "===== FINAL ====="
git rev-parse --short HEAD
echo "COMPANYOS_VERIFIED_OUTCOME_SCORING_V2=PASS"
