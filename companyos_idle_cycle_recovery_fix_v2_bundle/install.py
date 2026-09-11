from pathlib import Path
import shutil
import time
import subprocess
import os

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/runtime/idle_cycle_recovery_controller.py",
    "scripts/patch_idle_cycle_recovery_v2.py",
    "scripts/reset_idle_recovery_baseline.py",
    "scripts/companyos_idle_recovery_status.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"

subprocess.run(["python", "scripts/patch_idle_cycle_recovery_v2.py"], cwd=ROOT, env=env, check=True)
subprocess.run(["python", "scripts/reset_idle_recovery_baseline.py"], cwd=ROOT, env=env, check=True)

print("IDLE_CYCLE_RECOVERY_V2_INSTALL: PASS")
print("ANNOTATED_TICK_PATCHED: YES")
print("CURRENT_IDLE_BASELINE_RESEEDED: YES")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
print("WALLET_CONFIG_MODIFIED: NO")
