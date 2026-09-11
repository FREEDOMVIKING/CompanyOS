from pathlib import Path
import shutil, os, time

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/evolution/self_evolution_benchmark_judge.py",
    "scripts/companyos_self_evolution_benchmark_once.py",
    "scripts/companyos_self_evolution_benchmark_status.py",
    "scripts/companyos_self_evolution_benchmark.sh",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

os.chmod(ROOT / "scripts/companyos_self_evolution_benchmark.sh", 0o755)

print("SELF_EVOLUTION_BENCHMARK_JUDGE_INSTALL: PASS")
print("BEFORE_AFTER_RUNTIME_SCORING: ENABLED")
print("STRUCTURAL_COMPILE_CHECK: ENABLED")
print("PYTEST_BENCHMARK_CHECK: ENABLED")
print("PROMOTION_KEEP_ROLLBACK_DECISION: ENABLED")
print("BENCHMARK_LEDGER: ENABLED")
print("CORE_OVERWRITE_BY_DEFAULT: NO")
