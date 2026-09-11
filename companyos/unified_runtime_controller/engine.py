from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class UnifiedRuntimeController:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"runtime_controller.json"
    def run(self):
        count=0
        for p in Path("/proc").glob("[0-9]*"):
            try:
                if "companyos." in (p/"cmdline").read_text(errors="ignore"):count+=1
            except Exception:pass
        result={"generated_at":now(),"companyos_process_count":count,"mode":"observe_and_coordinate","status":"active"}
        write_json(self.out,result);return result
