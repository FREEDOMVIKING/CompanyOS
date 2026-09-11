#!/usr/bin/env python3
import json
from companyos.runtime.launch_controller import CompanyOSLaunchController
print(json.dumps(CompanyOSLaunchController().status(), indent=2, default=str))
