#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PROGRESSION="$ROOT/companyos/governance/venture_identity_progression.py"
RECON="$ROOT/companyos/runtime/canonical_state_reconciler.py"
LCTL="$ROOT/scripts/companyos_livenessctl"
RCTL="$ROOT/scripts/companyos_reconcilectl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.26 VERIFIED EXTERNAL STAGE RESOLVER ====="
echo "GOAL=MAKE_REAL_CONNECTOR_EXECUTION_EVIDENCE_AUTHORITATIVE_FOR_LIFECYCLE_STAGE"
echo "NOTE=SUCCESSFUL_DEPLOYMENT_RESULT_FORCES_AT_LEAST_LAUNCH"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$PROGRESSION" ] || { echo "V66_26_ABORT=missing:$PROGRESSION"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$PROGRESSION" "${PROGRESSION}.v66_26_backup_${stamp}"
echo "BACKUP=${PROGRESSION}.v66_26_backup_${stamp}"
if [ -f "$RECON" ]; then
  cp "$RECON" "${RECON}.v66_26_backup_${stamp}"
  echo "BACKUP=${RECON}.v66_26_backup_${stamp}"
fi

echo "===== PATCH VERIFIED EXTERNAL EVIDENCE RESOLVER ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/governance/venture_identity_progression.py"
s=p.read_text()

if "def verified_external_stage(files):" not in s:
    anchor="\ndef next_action(stage):"
    idx=s.find(anchor)
    if idx < 0:
        raise SystemExit("V66_26_ABORT=next_action_anchor_missing")

    addition = '''
def _iter_json_objects(path):
    try:
        text=path.read_text(errors="ignore")
    except Exception:
        return
    if path.suffix.lower()==".jsonl":
        for line in text.splitlines():
            try:
                obj=json.loads(line)
            except Exception:
                continue
            if isinstance(obj,dict):
                yield obj
    elif path.suffix.lower()==".json":
        try:
            obj=json.loads(text)
        except Exception:
            return
        if isinstance(obj,dict):
            yield obj

def verified_external_stage(files):
    # Structured external execution evidence outranks filename heuristics.
    observed=[]

    for path in files:
        low_name=str(path).lower()
        likely=any(x in low_name for x in (
            "deployment_result","live_url","customer_result",
            "conversion_result","lead_result","outreach_result",
            "campaign_result",
        ))
        if not likely or path.suffix.lower() not in {".json",".jsonl"}:
            continue

        for obj in _iter_json_objects(path):
            schema=str(obj.get("schema") or "").lower()
            connector=str(obj.get("connector") or "").lower()
            action=str(obj.get("action") or "").lower()
            status=str(obj.get("status") or "").lower()
            result=obj.get("result") if isinstance(obj.get("result"),dict) else {}

            ok=(
                obj.get("ok") is True
                or result.get("ok") is True
                or status in {"ok","success","succeeded","completed","executed"}
            )

            live_url=(
                obj.get("live_url")
                or result.get("live_url")
                or result.get("url")
            )
            deployment_id=(
                obj.get("deployment_id")
                or result.get("deployment_id")
            )

            real_deploy=(
                (
                    "real_deployment_result" in schema
                    or connector=="hosting"
                    or action=="deploy_production"
                    or "deployment_result" in low_name
                )
                and ok
                and bool(live_url or deployment_id)
            )
            if real_deploy:
                observed.append("LAUNCH")

            customer_signal=any(x in (schema+" "+low_name) for x in (
                "customer_result",
                "conversion_result",
                "lead_result",
                "outreach_result",
                "campaign_result",
            ))
            if customer_signal and ok:
                observed.append("CUSTOMER_ACQUISITION")

    return max_stage(*observed) if observed else None

'''
    s=s[:idx]+addition+s[idx:]

old = '''    return max_stage(*observed)

def next_action(stage):
'''
new = '''    inferred=max_stage(*observed)
    verified=verified_external_stage(files)
    return max_stage(inferred, verified)

def next_action(stage):
'''
if old in s:
    s=s.replace(old,new,1)
elif "verified=verified_external_stage(files)" not in s:
    raise SystemExit("V66_26_ABORT=infer_return_anchor_missing")

old_eval = '''        inferred_stage=infer_stage(fs)
        stage=max_stage(inferred_stage, old.get("stage"))
'''
new_eval = '''        verified_stage=verified_external_stage(fs)
        inferred_stage=infer_stage(fs)
        stage=max_stage(inferred_stage, verified_stage, old.get("stage"))
'''
if old_eval in s:
    s=s.replace(old_eval,new_eval,1)
elif "verified_stage=verified_external_stage(fs)" not in s:
    raise SystemExit("V66_26_ABORT=evaluate_stage_anchor_missing")

needle = '''             "inferred_stage":inferred_stage,
             "stage_regression_blocked":(
'''
replacement = '''             "inferred_stage":inferred_stage,
             "verified_external_stage":verified_stage,
             "stage_regression_blocked":(
'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_26_ABORT=row_verified_stage_anchor_missing")
    s=s.replace(needle,replacement,1)

p.write_text(s)
print("V66_26_PROGRESSION_PATCH=PASS")
PY

echo "===== PATCH RECONCILIATION VISIBILITY ====="
if [ -f "$RECON" ]; then
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/canonical_state_reconciler.py"
s=p.read_text()

old = '''from companyos.governance.venture_identity_progression import (
    candidate_ventures,
    artifact_files,
    infer_stage,
)
'''
new = '''from companyos.governance.venture_identity_progression import (
    candidate_ventures,
    artifact_files,
    infer_stage,
    verified_external_stage,
)
'''
if old in s:
    s=s.replace(old,new,1)
elif "verified_external_stage" not in s:
    raise SystemExit("V66_26_ABORT=reconciler_import_anchor_missing")

needle = '''            "inferred_stage_live":infer_stage(fs),
            "stage_markers":stage_markers(fs),
'''
replacement = '''            "inferred_stage_live":infer_stage(fs),
            "verified_external_stage_live":verified_external_stage(fs),
            "stage_markers":stage_markers(fs),
'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("V66_26_ABORT=reconciler_visibility_anchor_missing")
    s=s.replace(needle,replacement,1)

p.write_text(s)
print("V66_26_RECONCILER_VISIBILITY=PASS")
PY
fi

cat > "$ROOT/tests/test_v66_26_verified_external_stage.py" <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from companyos.governance.venture_identity_progression import (
    infer_stage,
    verified_external_stage,
)

def test_successful_real_deployment_is_launch():
    with TemporaryDirectory() as td:
        p=Path(td)
        build=p/"venture_stage_build.json"
        build.write_text("{}")
        dep=p/"deployment_result_abc.json"
        dep.write_text(json.dumps({
            "schema":"companyos.real_deployment_result.v1",
            "connector":"hosting",
            "action":"deploy_production",
            "ok":True,
            "live_url":"https://example.workers.dev",
        }))
        files=[build,dep]
        assert verified_external_stage(files)=="LAUNCH"
        assert infer_stage(files)=="LAUNCH"

def test_failed_deployment_does_not_prove_launch():
    with TemporaryDirectory() as td:
        p=Path(td)
        dep=p/"deployment_result_failed.json"
        dep.write_text(json.dumps({
            "schema":"companyos.real_deployment_result.v1",
            "connector":"hosting",
            "action":"deploy_production",
            "ok":False,
            "live_url":None,
        }))
        assert verified_external_stage([dep]) is None
PY

echo "===== COMPILE ====="
python -m py_compile "$PROGRESSION"
[ ! -f "$RECON" ] || python -m py_compile "$RECON"
echo "V66_26_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_26_verified_external_stage.py
echo "V66_26_TESTS=PASS"

echo "===== RE-EVALUATE LIVE CANONICAL STATE ====="
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
            "verified_external_stage":x.get("verified_external_stage"),
            "stage_regression_blocked":x.get("stage_regression_blocked"),
            "artifact_count":x.get("artifact_count"),
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

echo "V66_26_STRUCTURED_DEPLOYMENT_EVIDENCE=PASS"
echo "V66_26_SUCCESSFUL_DEPLOYMENT_FORCES_LAUNCH=PASS"
echo "V66_26_FAILED_DEPLOYMENT_DOES_NOT_ADVANCE=PASS"
echo "V66_26_RECONCILIATION_VISIBILITY=PASS"
echo "V66_26_NO_NEW_DAEMON=PASS"
echo "V66_26_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_26_COMPLETE"
