from pathlib import Path
import py_compile, tempfile

ROOT = Path.home() / "companyos"
files = [
    ROOT / "companyos/evolution/permanent_self_evolution_integration.py",
    ROOT / "scripts/companyos_permanent_self_evolution_once.py",
    ROOT / "scripts/companyos_permanent_self_evolution_status.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.evolution.permanent_self_evolution_integration import self_contained_test
probe_dir = ROOT / ".companyos_runtime" / "self_evolution" / "verify_probe"
probe_dir.mkdir(parents=True, exist_ok=True)
probe = probe_dir / "probe_module.py"
probe.write_text("def probe():\n    return True\n", encoding="utf-8")
test = self_contained_test(probe)
py_compile.compile(str(test), doraise=True)

try:
    from companyos.evolution.self_evolution_promotion_engine import promote
except Exception as exc:
    raise SystemExit(f"VERIFY_FAIL: promotion engine unavailable: {exc}")

print("SELF_CONTAINED_TEST_GENERATION: PASS")
print("PROMOTION_ENGINE_IMPORT: PASS")
print("PERMANENT_SELF_EVOLUTION_INTEGRATION_VERIFY: PASS")
