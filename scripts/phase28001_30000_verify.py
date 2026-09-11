#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.autonomy import AutonomousCompanyOperatingLoop,AutonomyGovernor,AutonomyStatus
g=AutonomyGovernor()
assert g.classify({"irreversible":True})["decision"]=="approval_required"
assert g.classify({"moves_money":True,"within_policy":False})["decision"]=="blocked"
root=Path(tempfile.mkdtemp())
r=AutonomousCompanyOperatingLoop(root).run_cycle({"treasury_policy_satisfied":True})
assert r["cycle"]==1
assert len(r["stages"])==15
assert AutonomyStatus().status()["status"]=="phase30000_autonomous_company_operating_loop_ready"
print(json.dumps({"success":True,"status":"phase28001_30000_verification_passed","cycle_status":"phase30000_autonomous_company_operating_loop_ready"},indent=2))
