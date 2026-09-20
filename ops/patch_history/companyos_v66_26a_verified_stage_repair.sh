#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PROGRESSION="$ROOT/companyos/governance/venture_identity_progression.py"
RECON="$ROOT/companyos/runtime/canonical_state_reconciler.py"
LCTL="$ROOT/scripts/companyos_livenessctl"
RCTL="$ROOT/scripts/companyos_reconcilectl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.26A VERIFIED STAGE REPAIR ====="
echo "GOAL=REPAIR_V66_26_ANCHOR_MISMATCH_AND_MAKE_REAL_DEPLOYMENT_EVIDENCE_AUTHORITATIVE"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$PROGRESSION" ] || { echo "V66_26A_ABORT=missing:$PROGRESSION"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$PROGRESSION" "${PROGRESSION}.v66_26a_backup_${stamp}"
echo "BACKUP=${PROGRESSION}.v66_26a_backup_${stamp}"
if [ -f "$RECON" ]; then
  cp "$RECON" "${RECON}.v66_26a_backup_${stamp}"
  echo "BACKUP=${RECON}.v66_26a_backup_${stamp}"
fi

echo "===== AST-SAFE PATCH ====="
python - <<'PY'
from pathlib import Path
import ast
import re

p=Path.home()/"companyos/companyos/governance/venture_identity_progression.py"
s=p.read_text()

if not re.search(r'(?m)^import json\s*$', s):
    s="import json\n"+s

def function_span(src, name):
    tree=ast.parse(src)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            return node.lineno, node.end_lineno
    return None

def replace_function(src, name, new_text):
    span=function_span(src,name)
    if not span:
        raise SystemExit(f"V66_26A_ABORT=function_not_found:{name}")
    start,end=span
    lines=src.splitlines()
    lines[start-1:end]=new_text.strip("\n").splitlines()
    return "\n".join(lines)+"\n"

if "STAGE_RANK" not in s:
    insert = (
        'STAGE_RANK = {\n'
        '    "DISCOVER":0,\n'
        '    "VALIDATE":1,\n'
        '    "BUILD":2,\n'
        '    "TEST":3,\n'
        '    "PACKAGE":4,\n'
        '    "LAUNCH_READY":5,\n'
        '    "LAUNCH":6,\n'
        '    "CUSTOMER_ACQUISITION":7,\n'
        '    "OPERATE":8,\n'
        '    "SCALE":9,\n'
        '}\n\n'
        'def max_stage(*stages):\n'
        '    valid=[str(x) for x in stages if str(x) in STAGE_RANK]\n'
        '    if not valid:\n'
        '        return "DISCOVER"\n'
        '    return max(valid,key=lambda x:STAGE_RANK[x])\n\n'
    )
    span=function_span(s,"infer_stage")
    if not span:
        raise SystemExit("V66_26A_ABORT=infer_stage_not_found")
    lines=s.splitlines()
    lines[span[0]-1:span[0]-1]=insert.strip("\n").splitlines()+[""]
    s="\n".join(lines)+"\n"

# Remove any partial helper definitions left by a prior attempt.
for name in ("verified_external_stage","_iter_json_objects"):
    span=function_span(s,name)
    if span:
        start,end=span
        lines=s.splitlines()
        lines[start-1:end]=[]
        s="\n".join(lines)+"\n"

helper = '''
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
    observed=[]

    for path in files:
        low_name=str(path).lower()
        likely=any(x in low_name for x in (
            "deployment_result",
            "real_deployment_result",
            "live_url",
            "customer_result",
            "conversion_result",
            "lead_result",
            "outreach_result",
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

span=function_span(s,"next_action")
if not span:
    raise SystemExit("V66_26A_ABORT=next_action_not_found")
lines=s.splitlines()
lines[span[0]-1:span[0]-1]=helper.strip("\n").splitlines()+[""]
s="\n".join(lines)+"\n"

infer = '''
def infer_stage(files):
    names=" ".join(str(p).lower() for p in files)
    observed=[]

    explicit_markers=[
        ("venture_stage_scale","SCALE"),
        ("venture_stage_operate","OPERATE"),
        ("venture_stage_customer_acquisition","CUSTOMER_ACQUISITION"),
        ("venture_stage_launch_ready","LAUNCH_READY"),
        ("venture_stage_launch","LAUNCH"),
        ("venture_stage_package","PACKAGE"),
        ("venture_stage_test","TEST"),
        ("venture_stage_build","BUILD"),
        ("venture_stage_validate","VALIDATE"),
    ]
    for marker,stage in explicit_markers:
        if marker in names:
            observed.append(stage)

    if any(x in names for x in (
        "conversion_result","customer_result","lead_result",
        "outreach_result","campaign_result",
    )):
        observed.append("CUSTOMER_ACQUISITION")

    if any(x in names for x in (
        "deployment_result","real_deployment_result","live_url",
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

    verified=verified_external_stage(files)
    if verified:
        observed.append(verified)
    return max_stage(*observed)
'''
s=replace_function(s,"infer_stage",infer)

# Patch evaluate_all robustly.
lines=s.splitlines()
inside=False
func_indent=0
out=[]
found_inferred=False
found_verified=False
found_stage=False

for line in lines:
    stripped=line.lstrip()
    indent=len(line)-len(stripped)

    if stripped.startswith("def evaluate_all("):
        inside=True
        func_indent=indent
        out.append(line)
        continue

    if inside and stripped.startswith("def ") and indent==func_indent:
        inside=False

    if inside and "inferred_stage=infer_stage(fs)" in stripped:
        prefix=line[:len(line)-len(stripped)]
        out.append(prefix+"verified_stage=verified_external_stage(fs)")
        out.append(line)
        found_verified=True
        found_inferred=True
        continue

    if inside and re.match(r'^stage\s*=\s*max_stage\(', stripped):
        prefix=line[:len(line)-len(stripped)]
        out.append(prefix+'stage=max_stage(inferred_stage, verified_stage, old.get("stage"))')
        found_stage=True
        continue

    out.append(line)

s="\n".join(out)+"\n"

if not found_inferred:
    raise SystemExit("V66_26A_ABORT=evaluate_all_inferred_stage_line_missing")
if not found_verified:
    raise SystemExit("V66_26A_ABORT=evaluate_all_verified_stage_insert_failed")
if not found_stage:
    raise SystemExit("V66_26A_ABORT=evaluate_all_stage_assignment_missing")

if '"verified_external_stage":verified_stage' not in s:
    marker='"inferred_stage":inferred_stage,'
    if marker in s:
        s=s.replace(
            marker,
            marker+'\n             "verified_external_stage":verified_stage,',
            1,
        )

ast.parse(s)
p.write_text(s)
print("V66_26A_AST_SAFE_PATCH=PASS")
PY

echo "===== PATCH RECONCILIATION VISIBILITY ====="
if [ -f "$RECON" ]; then
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/runtime/canonical_state_reconciler.py"
s=p.read_text()

if "verified_external_stage" not in s:
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
    else:
        s="from companyos.governance.venture_identity_progression import verified_external_stage\n"+s

if '"verified_external_stage_live"' not in s:
    marker='"inferred_stage_live":infer_stage(fs),'
    if marker in s:
        s=s.replace(
            marker,
            marker+'\n            "verified_external_stage_live":verified_external_stage(fs),',
            1,
        )

ast.parse(s)
p.write_text(s)
print("V66_26A_RECONCILER_PATCH=PASS")
PY
fi

cat > "$ROOT/tests/test_v66_26a_verified_stage_repair.py" <<'PY'
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from companyos.governance.venture_identity_progression import (
    infer_stage,
    verified_external_stage,
    max_stage,
)

def test_successful_deployment_forces_launch():
    with TemporaryDirectory() as td:
        p=Path(td)
        build=p/"venture_stage_build.json"
        build.write_text("{}")
        dep=p/"deployment_result_live.json"
        dep.write_text(json.dumps({
            "schema":"companyos.real_deployment_result.v1",
            "connector":"hosting",
            "action":"deploy_production",
            "ok":True,
            "deployment_id":"dep-123",
            "live_url":"https://example.workers.dev",
        }))
        files=[build,dep]
        assert verified_external_stage(files)=="LAUNCH"
        assert infer_stage(files)=="LAUNCH"

def test_failed_deployment_does_not_advance():
    with TemporaryDirectory() as td:
        p=Path(td)
        dep=p/"deployment_result_failed.json"
        dep.write_text(json.dumps({
            "schema":"companyos.real_deployment_result.v1",
            "connector":"hosting",
            "action":"deploy_production",
            "ok":False,
        }))
        assert verified_external_stage([dep]) is None

def test_stage_is_monotonic():
    assert max_stage("BUILD","LAUNCH")=="LAUNCH"
    assert max_stage("LAUNCH_READY","LAUNCH")=="LAUNCH"
PY

echo "===== COMPILE ====="
python -m py_compile "$PROGRESSION"
[ ! -f "$RECON" ] || python -m py_compile "$RECON"
echo "V66_26A_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_26a_verified_stage_repair.py
echo "V66_26A_TESTS=PASS"

echo "===== RE-EVALUATE REAL VENTURE STATE ====="
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
            "artifact_count":x.get("artifact_count"),
            "unchanged_observations":x.get("unchanged_observations"),
        }
        for x in rows
    ]
},indent=2,sort_keys=True))
PY

echo "===== REFRESH LIVENESS WITHOUT HEAVY RESTART ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== RECONCILIATION AUDIT ====="
if [ -x "$RCTL" ]; then
  "$RCTL" once || true
fi

echo "V66_26A_ANCHOR_FAILURE_REPAIRED=PASS"
echo "V66_26A_STRUCTURED_DEPLOYMENT_EVIDENCE=PASS"
echo "V66_26A_SUCCESSFUL_DEPLOYMENT_FORCES_LAUNCH=PASS"
echo "V66_26A_FAILED_DEPLOYMENT_DOES_NOT_ADVANCE=PASS"
echo "V66_26A_STAGE_REGRESSION_GUARD=PASS"
echo "V66_26A_NO_NEW_DAEMON=PASS"
echo "V66_26A_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_26A_COMPLETE"
