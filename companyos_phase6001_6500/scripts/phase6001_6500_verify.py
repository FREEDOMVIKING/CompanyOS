#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.hardening import *

root=Path(tempfile.mkdtemp())
health=HealthMatrix().evaluate([{"heartbeat":True,"error_rate":0,"saturation":.1,"backlog":1}])
assert health["healthy"] is True
slos=SLOEngine().evaluate({"availability":.999},{"availability":.99})
assert slos["all_met"] is True
assert ConfigValidator().validate({"x":1},["x"])["valid"] is True
assert SecretReferenceAudit().inspect({"api_key":"${API_KEY}"})["safe"] is True
assert RollbackManager().plan({"previous_artifact":"v1"})["ready"] is True
assert HardeningStatus().status()["status"]=="phase6500_production_hardening_observability_ready"
print(json.dumps({
 "success":True,
 "status":"phase6001_6500_verification_passed",
 "cycle_status":"phase6500_production_hardening_observability_ready"
},indent=2))
