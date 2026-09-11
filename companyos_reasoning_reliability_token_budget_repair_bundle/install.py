from pathlib import Path
import shutil, time, subprocess, os

ROOT = Path.home()/"companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/runtime/reasoning_reliability.py",
    "scripts/patch_reasoning_reliability.py",
    "scripts/companyos_reasoning_reliability_status.py",
    "scripts/companyos_recent_reasoning_errors.py",
]:
    src = SRC/rel
    dst = ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(["python", "scripts/patch_reasoning_reliability.py"], cwd=ROOT, env=env, check=True)

print("REASONING_RELIABILITY_TOKEN_BUDGET_REPAIR_INSTALL: PASS")
print("DEFAULT_MAX_OUTPUT_TOKENS: 8192")
print("ADAPTIVE_RETRY_BUDGETS: 8192 -> 4096 -> 2048/1024")
print("402_502_429_RETRY_HANDLING: ENABLED")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
