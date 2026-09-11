from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class AcquisitionScannerV2:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"acquisition_scanner.json"
    def run(self):
        ranking=read_json(self.home/"companyos_runtime"/"opportunity_engine"/"ranking.json",[])
        result={"generated_at":now(),"targets":[{"name":x.get("title"),"score":x.get("score",0)} for x in ranking[:10]],"purchase_status":"approval_required","status":"scanned"}
        write_json(self.out,result);return result
