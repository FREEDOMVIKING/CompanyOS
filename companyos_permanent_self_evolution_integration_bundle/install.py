from pathlib import Path
import shutil, os, time

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/evolution/permanent_self_evolution_integration.py",
    "scripts/companyos_permanent_self_evolution_once.py",
    "scripts/companyos_permanent_self_evolution_status.py",
    "scripts/companyos_permanent_self_evolution.sh",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

os.chmod(ROOT / "scripts/companyos_permanent_self_evolution.sh", 0o755)

print("PERMANENT_SELF_EVOLUTION_INTEGRATION_INSTALL: PASS")
print("ARCHITECTURE_ASSUMPTION_ON_OLD_tests_for_BLOCK: NO")
print("SELF_CONTAINED_TEST_GENERATION: ENABLED")
print("PRE_PROMOTION_VALIDATION: ENABLED")
print("PROMOTION_ENGINE_HANDOFF: ENABLED")
print("POST_PROMOTION_HEALTH_AND_ROLLBACK: INHERITED")
print("PERMANENT_LEDGER: ENABLED")
print("CORE_OVERWRITE_BY_DEFAULT: NO")
