from pathlib import Path
import shutil, time

ROOT = Path.home() / "companyos"
p = ROOT / "companyos" / "runtime" / "autonomous_ceo_orchestrator.py"
if not p.exists():
    raise SystemExit("FAIL: autonomous_ceo_orchestrator.py not found")

backup = p.with_name(p.name + ".bak.raw_capture." + str(int(time.time())))
shutil.copy2(p, backup)

s = p.read_text(encoding="utf-8")
marker = "# COMPANYOS_RAW_RESEARCH_CAPTURE_V1"

patch = """
# COMPANYOS_RAW_RESEARCH_CAPTURE_V1
try:
    from companyos.runtime.research_output_capture import install_orchestrator_capture as _install_companyos_research_capture
    _install_companyos_research_capture()
except Exception:
    pass
"""

if marker not in s:
    s = s.rstrip() + "\n\n" + patch.strip() + "\n"
    p.write_text(s, encoding="utf-8")

print("BACKUP:", backup)
print("ORCHESTRATOR_CAPTURE_PATCH: PASS")
print("PATCH_MODE: APPEND_ONLY_SAFE")
