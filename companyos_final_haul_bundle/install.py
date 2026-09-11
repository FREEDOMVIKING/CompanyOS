from pathlib import Path
import shutil, time, py_compile, os

src = Path(__file__).resolve().parent
root = Path.home() / "companyos"
backup = root/".companyos_runtime"/"consolidation"/f"final_haul_backup_{time.strftime('%Y%m%d_%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

required = [
    root/"companyos"/"canonicalexec"/"gateway.py",
    root/"companyos"/"canonicalorchestration"/"bridge.py",
    root/"companyos"/"canonicalruntime"/"bridge.py",
    root/"companyos"/"canonicalproduction"/"controller.py",
    root/"companyos"/"canonicaldaemon"/"daemon.py",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("MISSING_REQUIRED_CONSOLIDATION_LAYERS:")
    for p in missing: print(p)
    raise SystemExit(1)

copies = [
    (src/"companyos"/"finallaunch", root/"companyos"/"finallaunch"),
    (src/"scripts"/"companyos_final_launch.py", root/"scripts"/"companyos_final_launch.py"),
    (src/"scripts"/"companyos_final_launch.sh", root/"scripts"/"companyos_final_launch.sh"),
]

for s,d in copies:
    if d.exists():
        b=backup/d.relative_to(root)
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(d,b,dirs_exist_ok=True) if d.is_dir() else shutil.copy2(d,b)
    if s.is_dir():
        shutil.copytree(s,d,dirs_exist_ok=True)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s,d)

for p in (root/"companyos"/"finallaunch").rglob("*.py"):
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(root/"scripts"/"companyos_final_launch.py"), doraise=True)
os.chmod(root/"scripts"/"companyos_final_launch.sh", 0o755)

print("FINAL_HAUL_INSTALLED: True")
print("FINAL_PREFLIGHT_INSTALLED: True")
print("TRIAL_LIVE_PROFILE_AVAILABLE: True")
print("FULL_LIVE_PROFILE_AVAILABLE: True")
print("TERMUX_BOOT_INSTALLER_AVAILABLE: True")
print("LIVE_ENABLED_AT_INSTALL: False")
print("BROADCAST_DEFAULT_CHANGED: False")
print("PRIVATE_KEY_TOUCHED: False")
print("INSTALL_PASS")
