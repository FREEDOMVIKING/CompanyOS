#!/usr/bin/env python3
import json
from companyos.cycleops import OutcomeClassifier, CycleVerifier, ApprovalDeferment, CycleOpsStatus

jobs = [
    ({"job_id":"1","payload":{}}, {"success":True}),
    ({"job_id":"2","payload":{"requires_approval":True}}, {"success":False}),
    ({"job_id":"3","payload":{}}, {"success":False,"deduped":True}),
]

rows = []
verifier = CycleVerifier()

for job, result in jobs:
    normalized = ApprovalDeferment().normalize(job, result)
    rows.append({
        "job":job,
        "verification":verifier.verify_execution(job, normalized)
    })

summary = verifier.summarize_cycle(rows)

assert summary["total"] == 3
assert summary["resolved"] == 3
assert summary["unresolved"] == 0
assert summary["deferred_for_approval"] == 1
assert summary["deduplicated"] == 1
assert summary["cycle_verified"] is True
assert CycleOpsStatus().status()["status"] == "phase19000_cycle_closure_and_policy_resolution_ready"

print(json.dumps({
    "success":True,
    "status":"phase18001_19000_verification_passed",
    "cycle_status":"phase19000_cycle_closure_and_policy_resolution_ready",
    "summary":summary
}, indent=2))
