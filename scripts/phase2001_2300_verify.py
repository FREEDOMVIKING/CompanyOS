#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.integrations import *

root=Path(tempfile.mkdtemp())

reg=IntegrationRegistry(root)
reg.register("search","provider",["research"],True,{"priority":.9})
assert reg.available("research")

cv=CredentialVault(root)
assert cv.register_env_ref("search","SEARCH_API_KEY")["env_var"]=="SEARCH_API_KEY"

jobs=DepartmentRouter().route([{"task_type":"research","capability":"research"}])
assert jobs[0]["department"]=="research"

assert ParallelDispatcher().dispatch(jobs,2)["batch_count"]==1
assert ExternalActionApprovalGate().evaluate({"kind":"contract_signature"})["requires_approval"] is True
assert ResultVerifier().verify({"success":True,"x":1},["x"])["verified"] is True
assert ProviderHealthRegistry().rank([{"name":"a","availability":1,"error_rate":0,"quality":.8,"freshness":.8}])[0]["health_score"]>0
assert RuntimeStatus().status()["status"]=="phase2300_real_world_integration_orchestration_ready"

print(json.dumps({
    "success":True,
    "status":"phase2001_2300_verification_passed",
    "cycle_status":"phase2300_real_world_integration_orchestration_ready"
},indent=2))
