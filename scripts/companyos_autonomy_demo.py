#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.autonomy import AutonomousCompanyOperatingLoop
root=Path.home()/"companyos"
loop=AutonomousCompanyOperatingLoop(root)
print(json.dumps(loop.run_cycle({"treasury_policy_satisfied":True}),indent=2))
