#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase809_824 import *

sample = [
    {"mission_id":"mission_test_a","mission_type":"research","attempts":1,"status":"deferred","context":{"integration_test":True,"venture_id":"v1","objective":"x"}},
    {"mission_id":"m2","mission_type":"research","attempts":1,"status":"deferred","context":{"venture_id":"v2","objective":"y"}},
    {"mission_id":"m3","mission_type":"research","attempts":1,"status":"deferred","context":{"venture_id":"v2","objective":"y"}},
]

snap = QueueSnapshot().build(sample)
assert snap["count"] == 3
assert len(DeferredSelector().select(sample)) == 3
assert RetryLoopGuard().evaluate({"attempts":1})["allowed"] is True
assert MissionDeduplicator().dedupe(sample)["dropped"]
assert TestMissionRetirement().classify(sample[0])["retire"] is True
assert SupersessionPolicy().decide({"mission_id":"x"}, True)["retire_original"] is True
assert QueueCompactor().compact(sample)["retired"]
assert QueueDrainMetrics().compare({"count":3},{"count":2})["drained"] is True

root = Path(tempfile.mkdtemp(prefix="phase824_"))
assert RecoveryAudit(root).append({"event":"x"})["event"] == "x"
assert RuntimeStatus().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase809_824_verification_passed",
    "cycle_status":"phase824_queue_recovery_validation_promotion_ready"
}, indent=2))
