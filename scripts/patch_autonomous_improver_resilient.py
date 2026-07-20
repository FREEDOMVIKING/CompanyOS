#!/usr/bin/env python3
from pathlib import Path

root = Path.home() / "companyos"
candidates = [
    root / "companyos_phase261_268" / "autonomous_improver.py",
    root / "src" / "companyos_phase261_268" / "autonomous_improver.py",
]

target = next((p for p in candidates if p.exists()), None)
if target is None:
    raise SystemExit("ERROR: autonomous_improver.py not found")

text = target.read_text(encoding="utf-8")

old_import = "from companyos_phase253_260 import BuilderBridge"
new_import = "from companyos_phase269_276 import AutonomousRetryBridge"

text = text.replace(old_import, new_import)
text = text.replace(
    "self.builder = builder or BuilderBridge(self.root)",
    "self.builder = builder or AutonomousRetryBridge(self.root)",
)

target.write_text(text, encoding="utf-8")
print("PATCHED_AUTONOMOUS_IMPROVER:", target)
