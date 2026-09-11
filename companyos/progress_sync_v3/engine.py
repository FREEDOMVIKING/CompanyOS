from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class ProgressSyncV3:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"progress.json"
    def run(self):
        execution=read_json(self.runtime/"active_execution.json",{}).get("execution",{})
        milestones=read_json(self.runtime/"milestones.json",{}).get("milestones",[])
        active=sum(m.get("state")=="ACTIVE" for m in milestones);completed=sum(m.get("state")=="COMPLETED" for m in milestones);queued=sum(m.get("state")=="QUEUED" for m in milestones)
        result={"subject":execution.get("subject"),"execution_id":execution.get("execution_id"),"state":execution.get("state","PLANNING"),"progress_percent":int(completed/len(milestones)*100) if milestones else 0,"active":active,"completed":completed,"queued":queued,"blocked":0,"approvals":0,"updated_at":now(),"status":"synchronized"}
        write_json(self.home/".companyos_runtime"/"venture_progress_live.json",result)
        write_json(self.out,result)
        return result
