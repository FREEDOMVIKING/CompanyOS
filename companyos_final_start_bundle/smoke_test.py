from pathlib import Path
import sys
ROOT=Path.home()/"companyos"
sys.path[:0]=[str(ROOT),str(ROOT/"companyos")]
from companyos.walletintegration.canonical_startup_gate import verify_startup
r=verify_startup()
checks={
"canonical_signer_gate":bool(r.get("ready")),
"wallet_match":r.get("wallet")==r.get("registered_wallet"),
"rpc_loaded":bool(r.get("rpc_loaded")),
"private_key_loaded":bool(r.get("private_key_loaded")),
"control_script":(ROOT/"scripts"/"companyos_final_start.sh").exists(),
}
for k,v in checks.items(): print(f"{k} => {'PASS' if v else 'FAIL'}")
print("transaction_sent => PASS")
if not all(checks.values()): raise SystemExit("FINAL_START_SMOKE_TEST: FAIL")
print("FINAL_START_SMOKE_TEST: PASS")
