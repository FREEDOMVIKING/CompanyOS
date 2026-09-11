#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase545_560 import ServiceState, ServiceConfig, CEOWatchdog, HealthSnapshot

root = Path.home() / "companyos"
state = ServiceState(root).load()
config = ServiceConfig().load()
print(json.dumps({
    "watchdog": CEOWatchdog().evaluate(state, config["watchdog_stale_seconds"]),
    "snapshot": HealthSnapshot().build(state),
}, indent=2, default=str))
