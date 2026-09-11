#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase721_736 import EndToEndHarness, IntegrationReport

root=Path.home()/"companyos"
result=EndToEndHarness(root).run()
print(json.dumps(result,indent=2,default=str))
print("\n=== CONCISE REPORT ===")
print(json.dumps(IntegrationReport().build(result),indent=2,default=str))
