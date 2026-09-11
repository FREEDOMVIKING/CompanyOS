#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.expansionops import *

root=Path(tempfile.mkdtemp())
ranked=ExpansionRadar().rank([{
    "demand":1,"strategic_fit":1,"margin_potential":1,"speed_to_market":1,"risk":0
}])
assert ranked[0]["expansion_score"]==1
assert MarketEntryPlanner().plan(ranked[0])["steps"]
assert VentureReplicationEngine().replicate({"venture_id":"v"},"market")["new_venture_id"]
assert ExpansionAuthorityBoundary().evaluate({"kind":"enter_new_country"})["requires_approval"]
assert ExpansionOpsStatus().status()["status"]=="phase11500_autonomous_multi_venture_expansion_ready"

print(json.dumps({
    "success":True,
    "status":"phase11001_11500_verification_passed",
    "cycle_status":"phase11500_autonomous_multi_venture_expansion_ready"
},indent=2))
