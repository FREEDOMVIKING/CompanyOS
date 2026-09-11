from pathlib import Path
import py_compile
import os
import subprocess

ROOT = Path.home() / "companyos"
watchdog = ROOT / "companyos/runtime/productive_autonomy_watchdog.py"
controller = ROOT / "companyos/runtime/idle_cycle_recovery_controller.py"

for p in [watchdog, controller]:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")

py_compile.compile(str(watchdog), doraise=True)
py_compile.compile(str(controller), doraise=True)

text = watchdog.read_text(encoding="utf-8")
tick = text.find("def tick")
hook = text.find("maybe_recover_idle_cycles(", tick)
if tick < 0 or hook < 0 or hook - tick > 2200:
    raise SystemExit("VERIFY_FAIL: idle recovery hook not inside tick()")

print("RECOVERY_HOOK_INSIDE_TICK: PASS")

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
r = subprocess.run(
    ["python", "scripts/companyos_idle_recovery_status.py"],
    cwd=ROOT, env=env, text=True,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
print(r.stdout[:12000])
if r.returncode != 0:
    raise SystemExit("STATUS_VERIFY_FAIL")

print("IDLE_CYCLE_RECOVERY_V2_VERIFY: PASS")
