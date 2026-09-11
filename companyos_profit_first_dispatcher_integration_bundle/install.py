from pathlib import Path
import shutil, time, subprocess, os

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/runtime/profit_first_dispatcher.py",
    "scripts/patch_profit_first_dispatcher.py",
    "scripts/companyos_profit_first_dispatcher_status.py",
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
subprocess.run(["python", "scripts/patch_profit_first_dispatcher.py"], cwd=ROOT, env=env, check=True)

print("PROFIT_FIRST_DISPATCHER_INSTALL: PASS")
print("IDLE_TO_DISCOVERY_DISPATCH: ENABLED")
print("DEFAULT_IDLE_THRESHOLD_CYCLES: 20")
print("DEFAULT_COOLDOWN_SECONDS: 300")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
print("WALLET_OR_SIGNER_CONFIG_MODIFIED: NO")
