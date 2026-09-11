#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase481_496 import MissionQueue
from companyos_phase809_824 import QueueSnapshot, RuntimeStatus

root = Path.home() / "companyos"
missions = MissionQueue(root).load()
print(json.dumps({
    "runtime": RuntimeStatus().status(),
    "queue": QueueSnapshot().build(missions),
    "mission_ids": [m.get("mission_id") for m in missions],
}, indent=2))
