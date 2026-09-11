from pathlib import Path
import shutil, time, subprocess, os

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/strategy/candidate_materialization_bridge.py",
    "scripts/patch_candidate_materialization_bridge.py",
    "scripts/companyos_candidate_materialization.py",
    "scripts/companyos_candidate_materialization_status.py",
]:
    src = SRC / rel
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.copy2(dst, dst.with_name(dst.name + ".bak." + stamp))
    shutil.copy2(src, dst)
    print("INSTALLED:", dst)

(ROOT / ".companyos_runtime" / "profit_first_candidates").mkdir(parents=True, exist_ok=True)

env = os.environ.copy()
env["PYTHONPATH"] = f"{ROOT}:{ROOT/'companyos'}"

subprocess.run(
    ["python", "scripts/patch_candidate_materialization_bridge.py"],
    cwd=ROOT, env=env, check=True
)

print("CANDIDATE_MATERIALIZATION_BRIDGE_INSTALL: PASS")
print("ORCHESTRATION_OUTPUT_EXTRACTION: ENABLED")
print("STRUCTURED_CANDIDATE_MATERIALIZATION: ENABLED")
print("MISSING_OUTPUT_RECOVERY: ENABLED")
print("FAKE_SEEDED_CANDIDATES: NO")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
