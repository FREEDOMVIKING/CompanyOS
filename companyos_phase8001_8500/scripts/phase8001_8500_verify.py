#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.providerexec import *

root=Path(tempfile.mkdtemp())
reg=AdapterRegistry()
reg.register(HTTPProviderAdapter())
assert reg.get("http_generic") is not None
assert AdapterContract().validate(reg.get("http_generic"))["valid"]
assert CircuitBreaker().evaluate({"consecutive_failures":3})["open"]
assert not QuotaManager().evaluate(95,100)["within_quota"]
assert ProviderApprovalGate().evaluate({"kind":"production_deploy"})["requires_approval"]
assert ProviderExecutionStatus().status()["status"]=="phase8500_real_provider_execution_adapters_ready"

print(json.dumps({
    "success":True,
    "status":"phase8001_8500_verification_passed",
    "cycle_status":"phase8500_real_provider_execution_adapters_ready"
},indent=2))
