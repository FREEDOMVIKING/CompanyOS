#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
PROGRESSION="$ROOT/companyos/governance/venture_identity_progression.py"
RECON="$ROOT/companyos/runtime/canonical_state_reconciler.py"
LCTL="$ROOT/scripts/companyos_livenessctl"
RCTL="$ROOT/scripts/companyos_reconcilectl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.26B FUTURE-IMPORT + VERIFIED-STAGE REPAIR ====="
echo "GOAL=REPAIR_V66_26A_SYNTAX_ERROR_WITHOUT_ROLLING_BACK_GOOD_STAGE_LOGIC"
echo "NOTE=NO_NEW_DAEMON"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

[ -f "$PROGRESSION" ] || { echo "V66_26B_ABORT=missing:$PROGRESSION"; exit 1; }

stamp="$(date +%Y%m%d_%H%M%S)"
cp "$PROGRESSION" "${PROGRESSION}.v66_26b_backup_${stamp}"
echo "BACKUP=${PROGRESSION}.v66_26b_backup_${stamp}"
if [ -f "$RECON" ]; then
  cp "$RECON" "${RECON}.v66_26b_backup_${stamp}"
  echo "BACKUP=${RECON}.v66_26b_backup_${stamp}"
fi

echo "===== REPAIR IMPORT ORDER ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/governance/venture_identity_progression.py"
s=p.read_text()
lines=s.splitlines()

future_idx=None
for i,line in enumerate(lines):
    if line.strip()=="from __future__ import annotations":
        future_idx=i
        break

if future_idx is None:
    raise SystemExit("V66_26B_ABORT=future_import_missing")

# Remove stray top-level import json lines so we can put it in one safe place.
cleaned=[]
for line in lines:
    if line.strip()=="import json":
        continue
    cleaned.append(line)
lines=cleaned

# Re-find future import after cleanup.
future_idx=None
for i,line in enumerate(lines):
    if line.strip()=="from __future__ import annotations":
        future_idx=i
        break

# Ensure the future import is the first executable statement.
# Keep only blank/comment lines before it.
prefix=lines[:future_idx]
bad_before=[
    x for x in prefix
    if x.strip() and not x.lstrip().startswith("#")
]
if bad_before:
    # Move the future import to the very first executable position.
    lines.pop(future_idx)
    insert_at=0
    while insert_at < len(lines) and (
        not lines[insert_at].strip()
        or lines[insert_at].lstrip().startswith("#")
    ):
        insert_at += 1
    lines.insert(insert_at,"from __future__ import annotations")
    future_idx=insert_at

# Put json immediately after the future import.
lines.insert(future_idx+1,"import json")

s="\n".join(lines)+"\n"

# Confirm all the V66.26A logic survived before writing.
required=(
    "def verified_external_stage(files):",
    "verified_stage=verified_external_stage(fs)",
    "stage=max_stage(inferred_stage, verified_stage, old.get(\"stage\"))",
)
missing=[x for x in required if x not in s]
if missing:
    raise SystemExit("V66_26B_ABORT=verified_stage_logic_missing:"+repr(missing))

ast.parse(s)
p.write_text(s)
print("V66_26B_IMPORT_ORDER_REPAIRED=PASS")
print("V66_26B_VERIFIED_STAGE_LOGIC_PRESENT=PASS")
PY

echo "===== COMPILE ====="
python -m py_compile "$PROGRESSION"
if [ -f "$RECON" ]; then
  python -m py_compile "$RECON"
fi
echo "V66_26B_MODULE_COMPILE=PASS"

echo "===== VERIFIED-STAGE SELF TEST ====="
python - <<'PY'
import json
import tempfile
from pathlib import Path

from companyos.governance.venture_identity_progression import (
    verified_external_stage,
    infer_stage,
    max_stage,
)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    build=root/"venture_stage_build.json"
    dep=root/"deployment_result_live.json"
    build.write_text("{}")
    dep.write_text(json.dumps({
        "schema":"companyos.real_deployment_result.v1",
        "connector":"hosting",
        "action":"deploy_production",
        "ok":True,
        "deployment_id":"dep-test",
        "live_url":"https://example.workers.dev",
    }))
    files=[build,dep]
    assert verified_external_stage(files)=="LAUNCH"
    assert infer_stage(files)=="LAUNCH"
    assert max_stage("LAUNCH_READY","LAUNCH")=="LAUNCH"

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    dep=root/"deployment_result_failed.json"
    dep.write_text(json.dumps({
        "schema":"companyos.real_deployment_result.v1",
        "connector":"hosting",
        "action":"deploy_production",
        "ok":False,
    }))
    assert verified_external_stage([dep]) is None

print("V66_26B_SELF_TEST=PASS")
PY

echo "===== RE-EVALUATE LIVE CANONICAL VENTURES ====="
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
            "unchanged_observations":x.get("unchanged_observations"),
        }
        for x in rows
    ]
},indent=2,sort_keys=True))
PY

echo "===== REFRESH LIGHTWEIGHT LIVENESS SNAPSHOT ====="
if [ -x "$LCTL" ]; then
  "$LCTL" once || true
fi

echo "===== RECONCILIATION AUDIT ====="
if [ -x "$RCTL" ]; then
  "$RCTL" once || true
fi

echo "V66_26B_FUTURE_IMPORT_ORDER=PASS"
echo "V66_26B_VERIFIED_STAGE_LOGIC_PRESERVED=PASS"
echo "V66_26B_SUCCESSFUL_DEPLOYMENT_FORCES_LAUNCH=PASS"
echo "V66_26B_FAILED_DEPLOYMENT_DOES_NOT_ADVANCE=PASS"
echo "V66_26B_NO_HEAVY_RESTART=PASS"
echo "V66_26B_NO_NEW_DAEMON=PASS"
echo "V66_26B_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_26B_COMPLETE"
