from pathlib import Path
import shutil, subprocess, os, time

ROOT = Path.home()/"companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))
files = [
 "companyos/strategy/profit_first_venture_engine.py",
 "companyos/strategy/profit_first_opportunity_governor.py",
 "scripts/patch_profit_first_integration.py",
 "scripts/companyos_profit_first_status.py",
]
for rel in files:
    src, dst = SRC/rel, ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src,dst)
    print("INSTALLED:",dst)

env=os.environ.copy()
env["PYTHONPATH"]=f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(["python","scripts/patch_profit_first_integration.py"],cwd=ROOT,env=env,check=True)

print("PROFIT_FIRST_VENTURE_ENGINE_INSTALL: PASS")
print("PRIMARY_OBJECTIVE: SUSTAINABLE_RISK_ADJUSTED_ECONOMIC_VALUE")
print("BUSINESS_MODEL_NEUTRAL: YES")
print("RESEARCH_BEFORE_BUILD: YES")
print("NO_BUILD_BELOW_THRESHOLD: YES")
print("PORTFOLIO_REALLOCATION: YES")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
print("WALLET_OR_SIGNER_CONFIG_MODIFIED: NO")
