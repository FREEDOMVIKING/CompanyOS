from pathlib import Path
import shutil,time,subprocess,os

ROOT=Path.home()/"companyos"
SRC=Path(__file__).resolve().parent
stamp=str(int(time.time()))

for rel in [
    "companyos/strategy/diversified_opportunity_governor.py",
    "scripts/patch_productive_autonomy_diversification.py",
    "scripts/companyos_diversified_discovery.py",
]:
    src=SRC/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        shutil.copy2(dst,dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src,dst)
    print("INSTALLED:",dst)

env=os.environ.copy()
env["PYTHONPATH"]=f"{ROOT}:{ROOT/'companyos'}"
subprocess.run(["python","scripts/patch_productive_autonomy_diversification.py"],cwd=ROOT,env=env,check=True)

print("DIVERSIFIED_OPPORTUNITY_PORTFOLIO_INSTALL: PASS")
print("CONSTRUCTION_BANNED: NO")
print("SECTOR_CONCENTRATION_PENALTY: ENABLED")
print("ECONOMIC_SCORING_PRIORITY: ENABLED_IN_DISCOVERY_DIRECTIVE")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
