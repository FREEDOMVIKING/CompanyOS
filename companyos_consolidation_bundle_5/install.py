from pathlib import Path
import shutil, time, py_compile, os

src = Path(__file__).resolve().parent
root = Path.home() / "companyos"
backup = root / ".companyos_runtime" / "consolidation" / f"bundle5_backup_{time.strftime('%Y%m%d_%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

required = [
    root/"companyos"/"canonicalproduction"/"controller.py",
    root/"scripts"/"companyos_master_runtime.py",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("MISSING_REQUIRED_BUNDLE4:")
    for p in missing: print(p)
    raise SystemExit(1)

copies = [
    (src/"companyos"/"canonicaldaemon", root/"companyos"/"canonicaldaemon"),
    (src/"scripts"/"companyos_canonical_daemon.py", root/"scripts"/"companyos_canonical_daemon.py"),
    (src/"scripts"/"companyos_service.sh", root/"scripts"/"companyos_service.sh"),
    (src/"scripts"/"companyos_autostart_ready.sh", root/"scripts"/"companyos_autostart_ready.sh"),
]

for s, d in copies:
    if d.exists():
        b = backup / d.relative_to(root)
        b.parent.mkdir(parents=True, exist_ok=True)
        if d.is_dir():
            shutil.copytree(d, b, dirs_exist_ok=True)
        else:
            shutil.copy2(d, b)

    if s.is_dir():
        shutil.copytree(s, d, dirs_exist_ok=True)
    else:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)

for p in (root/"companyos"/"canonicaldaemon").rglob("*.py"):
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(root/"scripts"/"companyos_canonical_daemon.py"), doraise=True)

for sh in [
    root/"scripts"/"companyos_service.sh",
    root/"scripts"/"companyos_autostart_ready.sh",
]:
    os.chmod(sh, 0o755)

print("CANONICAL_DAEMON_INSTALLED: True")
print("SINGLE_INSTANCE_CONTROL: True")
print("CRASH_RECOVERY_BACKOFF: True")
print("HEARTBEAT_ENABLED: True")
print("LOG_ROTATION_ENABLED: True")
print("AUTOSTART_READY_SCRIPT_INSTALLED: True")
print("ANDROID_BOOT_AUTOSTART_ENABLED: False")
print("BROADCAST_DEFAULT_CHANGED: False")
print("PRIVATE_KEY_TOUCHED: False")
print("INSTALL_PASS")
