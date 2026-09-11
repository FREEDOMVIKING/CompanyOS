from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class SpecialistAssignmentV3:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"assignments.json"
    def run(self):
        milestones=read_json(self.runtime/"milestones.json",{}).get("milestones",[])
        pools=["research","strategy","product","marketing","operations"]
        result={"assignments":[{"milestone_id":m.get("id"),"specialist_pool":pools[i%5],"state":"ASSIGNED"} for i,m in enumerate(milestones)],"status":"assigned"}
        write_json(self.out,result)
        return result
