#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.executionops import CapabilityDiscovery
root = Path.home() / "companyos"
print(json.dumps({
    "success": True,
    "status": "real_capability_discovery_complete",
    "capabilities": CapabilityDiscovery(root).discover()
}, indent=2))
