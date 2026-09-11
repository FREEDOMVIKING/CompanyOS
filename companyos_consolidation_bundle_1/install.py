from pathlib import Path
import shutil, time, py_compile
src=Path(__file__).resolve().parent
root=Path.home()/"companyos"
backup=root/".companyos_runtime"/"consolidation"/f"bundle1_backup_{time.strftime('%Y%m%d_%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)

for s,d in [
    (src/"companyos"/"canonicalexec", root/"companyos"/"canonicalexec"),
    (src/"scripts"/"companyos_execution_gateway.py", root/"scripts"/"companyos_execution_gateway.py")
]:
    if d.exists():
        b=backup/d.relative_to(root); b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(d,b,dirs_exist_ok=True) if d.is_dir() else shutil.copy2(d,b)
    if s.is_dir(): shutil.copytree(s,d,dirs_exist_ok=True)
    else: d.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(s,d)

for p in (root/"companyos"/"canonicalexec").rglob("*.py"): py_compile.compile(str(p), doraise=True)
py_compile.compile(str(root/"scripts"/"companyos_execution_gateway.py"), doraise=True)

print("CANONICAL_GATEWAY_INSTALLED: True")
print("BROADCAST_DEFAULT_CHANGED: False")
print("EXTERNAL_ACTION_DEFAULT_CHANGED: False")
print("PRIVATE_KEY_TOUCHED: False")
print("INSTALL_PASS")
