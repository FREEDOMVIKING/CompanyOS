#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== CONTROLLED COMPANYOS AUTONOMOUS PUBLISH TEST ====="
python - <<'PY'
import json, sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root))
from companyos.website_deployer.engine import WebsiteDeployer

# Preserve any real venture-builder input and restore it after this test.
src=root/"companyos_runtime"/"venture_builder"/"latest_build.json"
backup=None
if src.exists():
    backup=src.read_bytes()
src.parent.mkdir(parents=True,exist_ok=True)

test={"title":"CompanyOS Autonomous Publish Verification",
      "purpose":"controlled hosting integration verification"}
src.write_text(json.dumps(test,indent=2))

try:
    result=WebsiteDeployer(root).run()
    print(json.dumps(result,indent=2,sort_keys=True))
    if result.get("status")!="published":
        raise SystemExit("FAIL: WebsiteDeployer did not report published")
    if not result.get("public_url"):
        raise SystemExit("FAIL: no public_url returned")
finally:
    if backup is None:
        src.unlink(missing_ok=True)
    else:
        src.write_bytes(backup)
PY

echo "===== DEPLOYMENT LEDGER TAIL ====="
tail -n 3 .companyos_runtime/deployment_ledger.jsonl || true
echo "===== LATEST DEPLOYMENT ====="
python -m json.tool .companyos_runtime/latest_deployment.json
echo "===== SUPERVISOR UNTOUCHED ====="
python scripts/companyos_hostingctl
echo "COMPANYOS_CONTROLLED_AUTONOMOUS_PUBLISH_TEST=PASS"
