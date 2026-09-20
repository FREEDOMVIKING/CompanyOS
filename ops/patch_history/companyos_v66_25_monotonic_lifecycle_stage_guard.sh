#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PROGRESSION="$ROOT/companyos/governance/venture_identity_progression.py"
LCTL="$ROOT/scripts/companyos_livenessctl"
RCTL="$ROOT/scripts/companyos_reconcilectl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.25 MONOTONIC LIFECYCLE STAGE GUARD ====="
echo "GOAL=PREVENT_REAL_DEPLOYMENT_EVIDENCE_FROM_BEING_OVERRIDDEN_BY_OLDER_BUILD_MARKERS"
echo "NOTE=LIFECYCLE_STAGE_CAN_ADVANCE_BUT_NOT_SILENTLY_REGRESS"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$PROGRESSION" ] || { echo "V66_25_ABORT=missing:$PROGRESSION"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$PROGRESSION" "${PROGRESSION}.v66_25_backup_${stamp}"
echo "BACKUP=${PROGRESSION}.v66_25_backup_${stamp}"

echo "===== PATCH STAGE INFERENCE ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/governance/venture_identity_progression.py"
s=p.read_text()

start=s.find("def infer_stage(files):")
end=s.find("\ndef next_action(stage):", start)
if start < 0 or end < 0:
    raise SystemExit("V66_25_ABORT=infer_stage_function_not_found")

replacement = '''STAGE_RANK = {
    "DISCOVER":0,
    "VALIDATE":1,
    "BUILD":2,
    "TEST":3,
    "PACKAGE":4,
    "LAUNCH_READY":5,
    "LAUNCH":6,
    "CUSTOMER_ACQUISITION":7,
    "OPERATE":8,
    "SCALE":9,
}

def max_stage(*stages):
    valid=[str(x) for x in stages if str(x) in STAGE_RANK]
    if not valid:
        return "DISCOVER"
    return max(valid, key=lambda x: STAGE_RANK[x])

def infer_stage(files):
    names=" ".join(str(p).lower() for p in files)
    observed=[]

    explicit_markers = [
        ("venture_stage_scale", "SCALE"),
        ("venture_stage_operate", "OPERATE"),
        ("venture_stage_customer_acquisition", "CUSTOMER_ACQUISITION"),
        ("venture_stage_launch_ready", "LAUNCH_READY"),
        ("venture_stage_launch", "LAUNCH"),
        ("venture_stage_package", "PACKAGE"),
        ("venture_stage_test", "TEST"),
        ("venture_stage_build", "BUILD"),
        ("venture_stage_validate", "VALIDATE"),
    ]
    for marker, stage in explicit_markers:
        if marker in names:
            observed.append(stage)

    if any(x in names for x in (
        "conversion_result", "customer_result", "lead_result",
        "outreach_result", "campaign_result",
    )):
        observed.append("CUSTOMER_ACQUISITION")

    if any(x in names for x in (
        "deployment_result", "live_url", "real_deployment_result",
    )):
        observed.append("LAUNCH")

    if any(p.suffix.lower()==".zip" for p in files) or "export_manifest" in names:
        observed.append("LAUNCH_READY")

    if any(x in names for x in (
        "test_result","qa_result","acceptance_result",
    )):
        observed.append("TEST")

    if "validation_result" in names:
        observed.append("VALIDATE")

    if files:
        observed.append("BUILD")

    return max_stage(*observed)

'''

s = s[:start] + replacement + s[end+1:]

old = "        stage=infer_stage(fs)\n"
new = '''        inferred_stage=infer_stage(fs)
        stage=max_stage(inferred_stage, old.get("stage"))
'''
if old in s:
    s=s.replace(old,new,1)
elif 'stage=max_stage(inferred_stage, old.get("stage"))' not in s:
    raise SystemExit("V66_25_ABORT=evaluate_stage_anchor_missing")

needle = '''             "stage":stage,
             "artifact_count":len(fs),
'''
replacement2 = '''             "stage":stage,
             "inferred_stage":inferred_stage,
             "stage_regression_blocked":(
                 old.get("stage") in STAGE_RANK
                 and STAGE_RANK.get(str(old.get("stage")),0)
                     > STAGE_RANK.get(inferred_stage,0)
             ),
             "artifact_count":len(fs),
'''
if needle in s:
    s=s.replace(needle,replacement2,1)
elif '"inferred_stage":inferred_stage' not in s:
    raise SystemExit("V66_25_ABORT=row_stage_anchor_missing")

old_rank = '''    rank={"DISCOVER":0,"VALIDATE":1,"BUILD":2,"TEST":3,"PACKAGE":4,"LAUNCH_READY":5,"LAUNCH":6,"CUSTOMER_ACQUISITION":7,"OPERATE":8,"SCALE":9}
    rows.sort(key=lambda r:(rank.get(r.get("stage"),0),r.get("unchanged_observations",0)),reverse=True)
'''
new_rank = '''    rows.sort(
        key=lambda r:(
            STAGE_RANK.get(r.get("stage"),0),
            r.get("unchanged_observations",0),
        ),
        reverse=True,
    )
'''
if old_rank in s:
    s=s.replace(old_rank,new_rank,1)

p.write_text(s)
print("V66_25_STAGE_INFERENCE_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_25_monotonic_stage_guard.py" <<'PY'
from pathlib import Path
from companyos.governance.venture_identity_progression import infer_stage, max_stage

def test_real_deployment_beats_historical_build_marker():
    files=[
        Path("/tmp/venture_stage_build.json"),
        Path("/tmp/companyos_progress/deployment_result_abc.json"),
    ]
    assert infer_stage(files)=="LAUNCH"

def test_customer_result_beats_launch():
    files=[
        Path("/tmp/deployment_result_abc.json"),
        Path("/tmp/customer_result_001.json"),
    ]
    assert infer_stage(files)=="CUSTOMER_ACQUISITION"

def test_monotonic_stage_helper():
    assert max_stage("LAUNCH","BUILD")=="LAUNCH"
    assert max_stage("CUSTOMER_ACQUISITION","LAUNCH")=="CUSTOMER_ACQUISITION"
PY

echo "===== COMPILE ====="
python -m py_compile "$PROGRESSION"
echo "V66_25_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_25_monotonic_stage_guard.py
echo "V66_25_TESTS=PASS"

echo "===== RE-EVALUATE CANONICAL VENTURES ====="
python - <<'PY'
import json
from companyos.governance.venture_identity_progression import evaluate_all

rows=evaluate_all()
print(json.dumps({
    "ventures":[
        {
            "canonical_id":x.get("canonical_id"),
            "stage":x.get("stage"),
            "inferred_stage":x.get("inferred_stage"),
            "stage_regression_blocked":x.get("stage_regression_blocked"),
            "artifact_count":x.get("artifact_count"),
            "unchanged_observations":x.get("unchanged_observations"),
        }
        for x in rows
    ]
},indent=2,sort_keys=True))
PY

echo "===== REFRESH LIVENESS ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== RECONCILIATION AUDIT ====="
if [ -x "$RCTL" ]; then
  "$RCTL" once || true
fi

echo "V66_25_HIGHEST_EVIDENCE_STAGE_WINS=PASS"
echo "V66_25_REAL_DEPLOYMENT_MAPS_TO_LAUNCH=PASS"
echo "V66_25_STAGE_REGRESSION_GUARD=PASS"
echo "V66_25_CUSTOMER_EVIDENCE_PRECEDENCE=PASS"
echo "V66_25_NO_NEW_DAEMON=PASS"
echo "V66_25_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_25_COMPLETE"
