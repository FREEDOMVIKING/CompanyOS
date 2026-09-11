#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.resilienceops import *

root=Path(tempfile.mkdtemp())
assert DependencyMap().build([{"name":"a","depends_on":["b"]}])["a"]==["b"]
assert FailureDomainAnalyzer().analyze([{"name":"a","failure_domain":"x"}])["single_domain_risk"]
assert BackupPolicy().evaluate({"name":"db","criticality":"critical"})["restore_test_required"]
assert DataIntegrityGuard().evaluate([{"name":"checksum","passed":True}])["integrity_ok"]
assert ResilienceAuthorityBoundary().evaluate({"kind":"disable_audit"})["requires_approval"]
assert ResilienceOpsStatus().status()["status"]=="phase12000_enterprise_resilience_continuity_command_ready"

print(json.dumps({
    "success":True,
    "status":"phase11501_12000_verification_passed",
    "cycle_status":"phase12000_enterprise_resilience_continuity_command_ready"
},indent=2))
