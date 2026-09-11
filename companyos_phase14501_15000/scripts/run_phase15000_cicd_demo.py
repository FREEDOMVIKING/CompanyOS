#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.cicdops import CEOCICDController

result = CEOCICDController(Path.home()/"companyos").run(
    version="15.0.0-demo",
    source_digest="demo_source_digest",
    checks={
        "lint":True,
        "static_analysis":True,
        "unit_tests":True,
        "integration_tests":True
    },
    scans={
        "security_scan":True,
        "dependency_scan":True,
        "secrets_scan":True
    },
    smoke_tests=True,
    staging_health=True,
    production_approval=False,
    deploy_success=True,
    postdeploy_health=True
)

print(json.dumps(result, indent=2, default=str))
