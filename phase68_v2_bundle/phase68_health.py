#!/usr/bin/env python3
import json
from companyos.runtime.health_supervisor import CompanyOSHealthSupervisor

result = CompanyOSHealthSupervisor().evaluate()
print(json.dumps(result, indent=2, default=str))
