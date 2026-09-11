from pathlib import Path
import py_compile, os, subprocess

ROOT = Path.home() / "companyos"
files = [
    ROOT/"companyos/runtime/idle_cycle_recovery_controller.py",
    ROOT/"companyos/runtime/productive_autonomy_watchdog.py",
    ROOT/"scripts/companyos_idle_recovery_status.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(files[0]), doraise=True)
py_compile.compile(str(files[1]), doraise=True)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
r = subprocess.run(
    ["python", "scripts/companyos_idle_recovery_status.py"],
    cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
print(r.stdout[:12000])
if r.returncode != 0:
    raise SystemExit("STATUS_VERIFY_FAIL")

print("IDLE_CYCLE_RECOVERY_VERIFY: PASS")
