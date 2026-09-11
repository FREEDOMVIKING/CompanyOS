#!/usr/bin/env python3
from pathlib import Path
root=Path.home()/"companyos"
candidates=[root/"src"/"companyos_phase705_720"/"persistent_runtime.py",root/"companyos_phase705_720"/"persistent_runtime.py"]
target=next((p for p in candidates if p.exists()),None)
if not target: raise SystemExit("ERROR: persistent_runtime.py not found")
text=target.read_text(encoding="utf-8")
if "from companyos_phase737_744 import ResilientExecutor" not in text:
    text=text.replace("from .integration_audit import IntegrationAudit\n","from .integration_audit import IntegrationAudit\nfrom companyos_phase737_744 import ResilientExecutor\n")
needle = "        result = self.cycle.run(mission)\n\n        remaining = [m for m in missions if m.get(\"mission_id\") != mission.get(\"mission_id\")]\n"
replacement = "        result = self.cycle.run(mission)\n\n        remaining = [m for m in missions if m.get(\"mission_id\") != mission.get(\"mission_id\")]\n\n        resilience = ResilientExecutor(self.state.path.parent.parent).handle(\n            mission, result, current_provider=((mission.get(\"context\") or {}).get(\"provider_hint\") or \"github\")\n        )\n        if resilience.get(\"handled\"):\n            deferred=resilience.get(\"mission\")\n            if deferred and deferred.get(\"mission_id\"):\n                remaining.append(deferred)\n            self.queue.save(remaining)\n            state=self.state.load()\n            state[\"cycles\"]=int(state.get(\"cycles\",0))+1\n            state[\"last_status\"]=resilience.get(\"status\")\n            state[\"last_venture_id\"]=result.get(\"venture_id\")\n            state[\"last_mission_id\"]=mission.get(\"mission_id\")\n            state[\"consecutive_failures\"]=int(state.get(\"consecutive_failures\",0))\n            self.state.save(state)\n            audit_payload={\"success\":True,\"status\":resilience.get(\"status\"),\"transient\":True,\"resilience\":resilience,\"original_result\":result}\n            self.audit.append(\"unified_cycle_deferred\",audit_payload)\n            return {\"success\":True,\"status\":\"unified_runtime_cycle_deferred\",\"executed\":1,\"remaining\":len(remaining),\"cycle\":audit_payload,\"state\":state}\n\n"
if needle not in text: raise SystemExit("ERROR: expected patch point not found; no patch applied")
target.write_text(text.replace(needle,replacement,1),encoding="utf-8")
print("PATCHED:",target)
