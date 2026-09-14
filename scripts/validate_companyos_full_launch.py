from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
sys.path.insert(0,str(ROOT))
from companyos.runtime.end_to_end_qualification import EndToEndQualification

result=EndToEndQualification(ROOT).run(recovery_test=True)
print(json.dumps(result,indent=2,sort_keys=True,default=str))
if not result.get("core_pass"):
    raise SystemExit(40)
print("COMPANYOS_FULL_4_STEP_CORE_VALIDATION=PASS")
