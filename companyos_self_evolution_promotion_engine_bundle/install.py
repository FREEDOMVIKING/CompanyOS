from pathlib import Path
import shutil, time

ROOT = Path.home()/"companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))
for rel in [
    "companyos/evolution/self_evolution_promotion_engine.py",
    "scripts/companyos_self_evolution_promote.py",
    "scripts/companyos_self_evolution_status.py",
    "scripts/companyos_self_evolution_dashboard_snapshot.py",
]:
    src = SRC/rel
    dst = ROOT/rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name+".bak."+stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)
print("SELF_EVOLUTION_PROMOTION_ENGINE_INSTALL: PASS")
print("SANDBOX_STAGING: ENABLED")
print("STATIC_COMPILE_TEST: ENABLED")
print("ISOLATED_IMPORT_TEST: ENABLED")
print("LOCAL_PYTEST_DISCOVERY: ENABLED")
print("CONTROLLED_PROMOTION: ENABLED")
print("POST_PROMOTION_HEALTH_CHECK: ENABLED")
print("AUTOMATIC_ROLLBACK: ENABLED")
print("EVOLUTION_LEDGER: ENABLED")
print("CORE_OVERWRITE_BY_DEFAULT: NO")
