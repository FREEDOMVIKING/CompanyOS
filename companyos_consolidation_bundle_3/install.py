from pathlib import Path
import shutil, time, py_compile

src = Path(__file__).resolve().parent
root = Path.home() / "companyos"
backup = root / ".companyos_runtime" / "consolidation" / f"bundle3_backup_{time.strftime('%Y%m%d_%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

requirements = [
    root/"companyos"/"canonicalexec"/"gateway.py",
    root/"companyos"/"canonicalorchestration"/"bridge.py",
]
missing = [str(p) for p in requirements if not p.exists()]
if missing:
    print("MISSING_REQUIRED_BUNDLES:")
    for p in missing:
        print(p)
    raise SystemExit(1)

copies = [
    (src/"companyos"/"canonicalruntime", root/"companyos"/"canonicalruntime"),
    (src/"scripts"/"companyos_canonical_runtime.py", root/"scripts"/"companyos_canonical_runtime.py"),
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

for p in (root/"companyos"/"canonicalruntime").rglob("*.py"):
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(root/"scripts"/"companyos_canonical_runtime.py"), doraise=True)

print("CANONICAL_RUNTIME_BRIDGE_INSTALLED: True")
print("BUNDLE1_GATEWAY_PRESENT: True")
print("BUNDLE2_ORCHESTRATION_PRESENT: True")
print("PHASE101_102_REPLACED: False")
print("PERMANENT_DAEMON_STARTED: False")
print("BROADCAST_DEFAULT_CHANGED: False")
print("PRIVATE_KEY_TOUCHED: False")
print("INSTALL_PASS")
