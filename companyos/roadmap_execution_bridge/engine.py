from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class RoadmapExecutionBridge:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"active_execution.json"
    def run(self):
        candidates=[self.home/"companyos_runtime"/"executive_roadmap.json",self.home/".companyos_runtime"/"executive_roadmap.json"]
        roadmap={}
        for p in candidates:
            roadmap=read_json(p,{})
            if roadmap:break
        subject=roadmap.get("subject") or roadmap.get("title") or "digital template business"
        eid="exec-"+str(abs(hash(subject)))
        execution={"execution_id":eid,"subject":subject,"state":"PLANNING","created_at":now(),"source":"executive_roadmap"}
        append_jsonl(self.home/".companyos_runtime"/"full_autonomy_journal.jsonl",{"ts":now(),"event":"roadmap_execution_created","event_type":"roadmap_execution_created","orchestration_id":eid,"state":execution})
        result={"phase":"70001-80000","execution":execution,"status":"linked"}
        write_json(self.out,result)
        return result
