from pathlib import Path
import sys, py_compile, json
ROOT=Path.home()/"companyos"
sys.path[:0]=[str(ROOT),str(ROOT/"companyos")]
files=[
ROOT/"companyos"/"walletintegration"/"canonical_startup_gate.py",
ROOT/"companyos"/"walletintegration"/"canonical_signer.py",
ROOT/"scripts"/"companyos_final_start.sh",
ROOT/"scripts"/"companyos_final_preflight.py",
]
for p in files:
    if not p.exists(): raise SystemExit("VERIFY_FAIL missing: "+str(p))
    if p.suffix==".py": py_compile.compile(str(p),doraise=True)
from companyos.walletintegration.canonical_startup_gate import verify_startup
r=verify_startup()
print(json.dumps(r,indent=2))
if not r.get("ready"): raise SystemExit("VERIFY_FAIL startup gate")
print("FINAL_START_VERIFY: PASS")
