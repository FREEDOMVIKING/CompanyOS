#!/usr/bin/env python3
from pathlib import Path

root=Path.home()/"companyos"
candidates=[
    root/"src"/"companyos_phase705_720"/"closed_loop_cycle.py",
    root/"companyos_phase705_720"/"closed_loop_cycle.py",
]
target=next((p for p in candidates if p.exists()),None)
if not target:
    raise SystemExit("ERROR: closed_loop_cycle.py not found")

text=target.read_text(encoding="utf-8")
if "from companyos_phase761_776 import CEOResearchRuntimeBridge" not in text:
    text=text.replace(
        "from .context_bus import ContextBus\n",
        "from .context_bus import ContextBus\nfrom companyos_phase761_776 import CEOResearchRuntimeBridge\n"
    )

needle='''        executed = self.executor.execute(mission)
        venture_id = (
'''
replacement='''        executed = self.executor.execute(mission)

        research_quality = None
        if mission.get("mission_type") == "research":
            providers = [
                {"name":"github","availability":0.8,"recent_failures":0},
                {"name":"hacker_news","availability":0.9,"recent_failures":0},
                {"name":"public_web","availability":0.95,"recent_failures":0},
                {"name":"local_cache","availability":1.0,"recent_failures":0},
            ]
            research_quality = CEOResearchRuntimeBridge(self.executor.runner.root if hasattr(self.executor.runner, "root") else self.lifecycle.bridge.store.root).evaluate(
                mission, executed.get("result") or {}, providers
            )

        venture_id = (
'''
if needle not in text:
    raise SystemExit("ERROR: expected closed-loop patch point not found")

text=text.replace(needle,replacement,1)

needle2='''        outcome = self.outcomes.normalize(executed["result"])
        lifecycle = self.lifecycle.apply(venture_id, outcome)
'''
replacement2='''        outcome = self.outcomes.normalize(executed["result"])
        if research_quality:
            outcome.update(research_quality.get("lifecycle_evidence") or {})
        lifecycle = self.lifecycle.apply(venture_id, outcome)
'''
if needle2 not in text:
    raise SystemExit("ERROR: lifecycle patch point not found")

text=text.replace(needle2,replacement2,1)

needle3='''            "execution": executed,
            "outcome": outcome,
'''
replacement3='''            "execution": executed,
            "research_quality": research_quality,
            "outcome": outcome,
'''
if needle3 in text:
    text=text.replace(needle3,replacement3,1)

target.write_text(text,encoding="utf-8")
print("PATCHED:",target)
