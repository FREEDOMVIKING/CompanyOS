#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.executionops import CapabilityDiscovery

root = Path.home() / "companyos"
caps = CapabilityDiscovery(root).discover()

print(json.dumps({
    "success": True,
    "status": "execution_wiring_preview",
    "discovered_capabilities": caps,
    "launch_candidates": {
        k:v for k,v in caps.items() if k in {"release","deployment","marketing"}
    },
    "note": "Preview only. This command does not trigger external side effects."
}, indent=2))
