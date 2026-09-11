from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class MilestoneGeneratorV3:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"milestones.json"
    def run(self):
        execution=read_json(self.runtime/"active_execution.json",{}).get("execution",{})
        names=["Validate market evidence","Define offer and customer","Build minimum viable product","Prepare sales and launch assets","Run launch-readiness review"]
        milestones=[{"id":f"m{i+1}","name":n,"subject":execution.get("subject"),"state":"ACTIVE" if i==0 else "QUEUED","progress":0} for i,n in enumerate(names)]
        result={"execution_id":execution.get("execution_id"),"milestones":milestones,"status":"generated"}
        write_json(self.out,result)
        return result
