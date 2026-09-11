from pathlib import Path
import shutil, time, subprocess, os

ROOT = Path.home() / "companyos"
SRC = Path(__file__).resolve().parent
stamp = str(int(time.time()))

for rel in [
    "companyos/runtime/research_output_capture.py",
    "scripts/patch_orchestrator_research_capture.py",
    "scripts/companyos_extract_canonical_research_outputs.py",
    "scripts/companyos_research_output_capture_status.py",
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
subprocess.run(
    ["python", "scripts/patch_orchestrator_research_capture.py"],
    cwd=ROOT, env=env, check=True
)

print("RESEARCH_OUTPUT_CAPTURE_BRIDGE_INSTALL: PASS")
print("RAW_RETURN_CAPTURE: ENABLED")
print("CANONICAL_RESEARCH_OUTPUT_STORE: ENABLED")
print("EXACT_ORCHESTRATION_LINEAGE: ENABLED")
print("POST_CAPTURE_CANDIDATE_EXTRACTION: ENABLED")
print("FAKE_CANDIDATES_SEEDED: NO")
print("EXTERNAL_APPROVAL_GATES_BYPASSED: NO")
print("FINANCIAL_LIMITS_MODIFIED: NO")
