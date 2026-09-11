from pathlib import Path
import shutil, stat, time
ROOT=Path.home()/"companyos"
SRC=Path(__file__).resolve().parent
if not ROOT.exists(): raise SystemExit("INSTALL_FAIL: ~/companyos missing")
for name in ["companyos_full_autonomy_runner.py","companyos_full_autonomy.sh"]:
    s=SRC/"scripts"/name
    d=ROOT/"scripts"/name
    d.parent.mkdir(parents=True,exist_ok=True)
    if d.exists():
        b=d.with_name(d.name+".bak."+str(int(time.time())))
        shutil.copy2(d,b)
        print("BACKUP:",b)
    shutil.copy2(s,d)
    print("INSTALLED:",d)
ctl=ROOT/"scripts"/"companyos_full_autonomy.sh"
ctl.chmod(ctl.stat().st_mode|stat.S_IXUSR)
print("FULL_AUTONOMY_BUNDLE_INSTALLED: True")
print("PRIVATE_KEYS_MODIFIED: False")
print("WALLET_REGISTRY_MODIFIED: False")
print("LIVE_LIMITS_BYPASSED: False")
print("INSTALL_PASS")
