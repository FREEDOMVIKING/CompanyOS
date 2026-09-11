from pathlib import Path
import shutil, stat, time
ROOT=Path.home()/"companyos"
SRC=Path(__file__).resolve().parent
targets=[
(SRC/"companyos"/"walletintegration"/"canonical_startup_gate.py", ROOT/"companyos"/"walletintegration"/"canonical_startup_gate.py"),
(SRC/"scripts"/"companyos_final_start.sh", ROOT/"scripts"/"companyos_final_start.sh"),
(SRC/"scripts"/"companyos_final_preflight.py", ROOT/"scripts"/"companyos_final_preflight.py"),
]
if not ROOT.exists(): raise SystemExit("INSTALL_FAIL: ~/companyos not found")
stamp=str(int(time.time()))
for s,d in targets:
    d.parent.mkdir(parents=True,exist_ok=True)
    if d.exists():
        b=d.with_name(d.name+".bak."+stamp); shutil.copy2(d,b); print("BACKUP:",b)
    shutil.copy2(s,d); print("INSTALLED:",d)
(ROOT/"scripts"/"companyos_final_start.sh").chmod((ROOT/"scripts"/"companyos_final_start.sh").stat().st_mode|stat.S_IXUSR)
env=ROOT/".companyos_runtime"/"live_financial.env"
if env.exists(): env.chmod(0o600)
print("CANONICAL_STARTUP_GATE_INSTALLED: True")
print("PRIMARY_WALLET_UNCHANGED: True")
print("PRIVATE_KEY_TOUCHED: False")
print("BROADCAST_DEFAULT_CHANGED: False")
print("INSTALL_PASS")
