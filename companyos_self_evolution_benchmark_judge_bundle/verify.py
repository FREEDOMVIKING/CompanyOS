from pathlib import Path
import py_compile

ROOT = Path.home() / "companyos"
files = [
    ROOT / "companyos/evolution/self_evolution_benchmark_judge.py",
    ROOT / "scripts/companyos_self_evolution_benchmark_once.py",
    ROOT / "scripts/companyos_self_evolution_benchmark_status.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.evolution.self_evolution_benchmark_judge import runtime_snapshot, score_snapshot
snap = runtime_snapshot()
score = score_snapshot(snap)
if not (0.0 <= score <= 1.0):
    raise SystemExit("VERIFY_FAIL: invalid benchmark score")

print("RUNTIME_SNAPSHOT: PASS")
print("BENCHMARK_SCORE_RANGE: PASS")
print("CURRENT_SCORE:", score)
print("SELF_EVOLUTION_BENCHMARK_JUDGE_VERIFY: PASS")
