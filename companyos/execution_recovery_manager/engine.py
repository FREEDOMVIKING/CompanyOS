from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class ExecutionRecoveryManager:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"recovery.json"
    def run(self):
        required=["active_execution.json","milestones.json","assignments.json","artifacts.json","evidence.json","progress.json"]
        missing=[n for n in required if not (self.runtime/n).exists()]
        result={"checked_at":now(),"missing":missing,"recovery_needed":bool(missing),"status":"healthy" if not missing else "repair_required"}
        write_json(self.out,result)
        return result
