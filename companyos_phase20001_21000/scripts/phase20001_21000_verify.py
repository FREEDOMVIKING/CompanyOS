#!/usr/bin/env python3
import json
from companyos.recoveryops import DiagnosticEngine, RetryPolicy, MissingInputHandler, RecoveryOpsStatus

job = {
    "job_id":"x",
    "department":"customer_success",
    "payload":{"instruction":"Analyze issue"}
}
execution = {
    "success":False,
    "analysis":"Need more information. Please provide details."
}
verification = {"passed":False}

d = DiagnosticEngine().diagnose(job, execution, verification)
assert d["kind"] == "missing_input"
assert d["recoverable"] is True

r = RetryPolicy().decision(d, 0)
assert r["retry"] is True
assert r["next_attempt"] == 1

enriched = MissingInputHandler().enrich(job)
assert enriched["payload"]["recovery_enriched"] is True
assert "bounded internal assumptions" in enriched["payload"]["instruction"]

assert RecoveryOpsStatus().status()["status"] == "phase21000_autonomous_recovery_layer_ready"

print(json.dumps({
    "success":True,
    "status":"phase20001_21000_verification_passed",
    "cycle_status":"phase21000_autonomous_recovery_layer_ready"
}, indent=2))
