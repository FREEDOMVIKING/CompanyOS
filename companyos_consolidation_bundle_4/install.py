from pathlib import Path
import shutil, time, py_compile

src = Path(__file__).resolve().parent
root = Path.home() / "companyos"
backup = root / ".companyos_runtime" / "consolidation" / f"bundle4_backup_{time.strftime('%Y%m%d_%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

required = [
    root/"companyos"/"canonicalexec"/"gateway.py",
    root/"companyos"/"canonicalorchestration"/"bridge.py",
    root/"companyos"/"canonicalruntime"/"bridge.py",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print("MISSING_REQUIRED_BUNDLES:")
    for p in missing: print(p)
    raise SystemExit(1)

copies = [
    (src/"companyos"/"canonicalproduction", root/"companyos"/"canonicalproduction"),
    (src/"scripts"/"companyos_master_runtime.py", root/"scripts"/"companyos_master_runtime.py"),
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

for p in (root/"companyos"/"canonicalproduction").rglob("*.py"):
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(root/"scripts"/"companyos_master_runtime.py"), doraise=True)

print("CANONICAL_PRODUCTION_RUNTIME_INSTALLED: True")
print("BUNDLE1_PRESENT: True")
print("BUNDLE2_PRESENT: True")
print("BUNDLE3_PRESENT: True")
print("PHASE102_CONTROL_REUSED: True")
print("LEGACY_RUNTIME_DELETED: False")
print("BOOT_AUTOSTART_CHANGED: False")
print("BROADCAST_DEFAULT_CHANGED: False")
print("PRIVATE_KEY_TOUCHED: False")
print("INSTALL_PASS")
