#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase873_888 import *
root=Path(tempfile.mkdtemp())
task={"task":{"dimension":"pricing_validation","query":"pricing"},"provider_chain":["public_web"]}
r=ProviderTaskRouter().route(task); assert r["provider_chain"]
assert TaskResultNormalizer().normalize([{"task":task,"batches":[{"items":[{"id":"1"}]}]}])
assert RoundEvidenceStore(root).save("m",1,[{"id":"1"}])["count"]==1
hist=ConvergenceTracker().append([],{"scores":{"validation_confidence":.6},"decision":"REVISE"})
assert DecisionConvergence().evaluate(hist)["converged"] is False
assert BoundedRoundPolicy().evaluate(1)["allowed"]
assert VentureArchiveBridge().build("KILL",.2)["archive"]
assert RuntimeStatus().status()["success"]
print(json.dumps({"success":True,"status":"phase873_888_verification_passed",
"cycle_status":"phase888_revalidation_execution_convergence_ready"},indent=2))
