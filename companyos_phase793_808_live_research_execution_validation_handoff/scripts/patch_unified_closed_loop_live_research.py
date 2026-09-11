#!/usr/bin/env python3
from pathlib import Path

root = Path.home() / "companyos"
candidates = [
    root / "src" / "companyos_phase705_720" / "closed_loop_cycle.py",
    root / "companyos_phase705_720" / "closed_loop_cycle.py",
]
target = next((p for p in candidates if p.exists()), None)
if not target:
    raise SystemExit("ERROR: closed_loop_cycle.py not found")

text = target.read_text(encoding="utf-8")

import_line = "from companyos_phase793_808 import CEOResearchExecutionBridge\n"
if import_line not in text:
    anchor = "from companyos_phase761_776 import CEOResearchRuntimeBridge\n"
    if anchor in text:
        text = text.replace(anchor, anchor + import_line, 1)
    else:
        # Add after first import block safely.
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = i + 1
            else:
                if insert_at:
                    break
        lines.insert(insert_at, import_line.rstrip())
        text = "\n".join(lines) + "\n"

marker = "# PHASE793_808_LIVE_RESEARCH_INTEGRATION"
if marker not in text:
    needle = '        executed = self.executor.execute(mission)\n'
    if needle not in text:
        raise SystemExit("ERROR: execution anchor not found")

    block = '''        # PHASE793_808_LIVE_RESEARCH_INTEGRATION
        live_research = None
        if mission.get("mission_type") == "research":
            live_research = CEOResearchExecutionBridge(Path.home() / "companyos").process(
                mission,
                executed.get("result") or {},
            )
'''
    text = text.replace(needle, needle + block, 1)

# Add live research output to return payload if not already present.
if '"live_research": live_research,' not in text:
    needle2 = '            "execution": executed,\n'
    if needle2 in text:
        text = text.replace(
            needle2,
            needle2 + '            "live_research": live_research,\n',
            1
        )

target.write_text(text, encoding="utf-8")
print("PATCHED:", target)
