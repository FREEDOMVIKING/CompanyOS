from pathlib import Path
import py_compile, sys, json
ROOT=Path.home()/"companyos"
sys.path[:0]=[str(ROOT),str(ROOT/"companyos")]
files=[
ROOT/"scripts"/"companyos_full_autonomy_runner.py",
ROOT/"scripts"/"companyos_full_autonomy.sh",
ROOT/"companyos"/"walletintegration"/"canonical_signer.py",
ROOT/"companyos"/"walletintegration"/"canonical_startup_gate.py"
]
for p in files:
    print(p,"=>","PASS" if p.exists() else "FAIL")
    if not p.exists(): raise SystemExit("VERIFY_FAIL")
    if p.suffix==".py": py_compile.compile(str(p),doraise=True)
from companyos.walletintegration.canonical_startup_gate import verify_startup
r=verify_startup()
print(json.dumps(r,indent=2,default=str))
if not r.get("ready"): raise SystemExit("VERIFY_FAIL: startup gate")
print("FULL_AUTONOMY_VERIFY: PASS")
print("TRANSACTION_SENT: NO")
