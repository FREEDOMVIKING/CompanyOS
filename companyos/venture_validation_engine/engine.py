from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class VentureValidationEngine:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"validation.json"
    def run(self):
        p=read_json(self.runtime/"progress.json",{});a=read_json(self.runtime/"artifacts.json",{})
        checks={"execution_linked":bool(p.get("execution_id")),"milestones_present":p.get("active",0)+p.get("queued",0)+p.get("completed",0)>0,"artifacts_present":bool(a.get("artifact_dir"))}
        result={"checks":checks,"passed":all(checks.values()),"status":"validated"}
        write_json(self.out,result)
        return result
