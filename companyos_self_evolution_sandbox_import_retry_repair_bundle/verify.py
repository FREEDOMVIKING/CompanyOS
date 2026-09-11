from pathlib import Path
import py_compile
ROOT = Path.home() / "companyos"
files = [
    ROOT / "companyos/evolution/self_evolution_sandbox_retry_repair.py",
    ROOT / "companyos/evolution/self_evolution_generator.py",
    ROOT / "companyos/evolution/self_evolution_promotion_engine.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)
from companyos.evolution.self_evolution_sandbox_retry_repair import repair_all_generated_tests
r = repair_all_generated_tests()
print("GENERATED_TEST_REWRITE_FUNCTION: PASS")
print("GENERATED_PAIRS_FOUND:", r["generated_pairs_found"])
print("PATCHED_TESTS:", r["patched"])
print("SELF_EVOLUTION_SANDBOX_IMPORT_RETRY_REPAIR_VERIFY: PASS")
