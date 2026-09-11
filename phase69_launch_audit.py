#!/usr/bin/env python3
import json
from companyos.runtime.launch_readiness_audit import LaunchReadinessAudit

result = LaunchReadinessAudit().run()
print(json.dumps(result, indent=2, default=str))
