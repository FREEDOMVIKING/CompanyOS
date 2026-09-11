from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class LaunchReadinessEngine:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"launch_readiness.json"
    def run(self):
        v=read_json(self.runtime/"validation.json",{});p=read_json(self.runtime/"progress.json",{})
        blockers=[]
        if not v.get("passed"):blockers.append("validation_failed")
        if p.get("completed",0)<3:blockers.append("insufficient_completed_milestones")
        result={"ready":not blockers,"blockers":blockers,"external_launch":"approval_required","status":"ready" if not blockers else "not_ready"}
        write_json(self.out,result)
        return result
