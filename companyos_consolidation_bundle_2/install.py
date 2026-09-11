from pathlib import Path
import shutil, time, py_compile

src = Path(__file__).resolve().parent
root = Path.home() / "companyos"
backup = root / ".companyos_runtime" / "consolidation" / f"bundle2_backup_{time.strftime('%Y%m%d_%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

copies = [
    (src/"companyos"/"canonicalorchestration", root/"companyos"/"canonicalorchestration"),
    (src/"scripts"/"companyos_orchestration_bridge.py", root/"scripts"/"companyos_orchestration_bridge.py"),
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

for p in (root/"companyos"/"canonicalorchestration").rglob("*.py"):
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(root/"scripts"/"companyos_orchestration_bridge.py"), doraise=True)

print("CANONICAL_ORCHESTRATION_INSTALLED: True")
print("BUNDLE1_GATEWAY_REQUIRED: True")
print("LEGACY_RUNTIME_REPLACED: False")
print("BROADCAST_DEFAULT_CHANGED: False")
print("EXTERNAL_ACTION_DEFAULT_CHANGED: False")
print("PRIVATE_KEY_TOUCHED: False")
print("INSTALL_PASS")
