from pathlib import Path
import py_compile, importlib

ROOT = Path.home() / "companyos"
files = [
    ROOT / "companyos/runtime/research_output_capture.py",
    ROOT / "companyos/runtime/autonomous_ceo_orchestrator.py",
    ROOT / "scripts/companyos_extract_canonical_research_outputs.py",
]
for p in files:
    print(p, "=>", "PASS" if p.exists() else "FAIL")
    if not p.exists():
        raise SystemExit("VERIFY_FAIL")
    py_compile.compile(str(p), doraise=True)

from companyos.runtime.research_output_capture import install_orchestrator_capture
ok = install_orchestrator_capture()
if not ok:
    raise SystemExit("VERIFY_FAIL: capture wrapper install failed")

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
wrapped = getattr(AutonomousCEOOrchestrator.start, "_companyos_raw_capture_wrapped", False)
if not wrapped:
    raise SystemExit("VERIFY_FAIL: start() not wrapped")

print("ORCHESTRATOR_START_WRAPPED: PASS")
print("RESEARCH_OUTPUT_CAPTURE_BRIDGE_VERIFY: PASS")
