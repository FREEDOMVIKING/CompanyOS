from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class ExecutionEvidenceLinker:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"evidence.json"
    def run(self):
        execution=read_json(self.runtime/"active_execution.json",{}).get("execution",{})
        milestones=read_json(self.runtime/"milestones.json",{}).get("milestones",[])
        artifacts=read_json(self.runtime/"artifacts.json",{})
        ev={"execution_id":execution.get("execution_id"),"linked_milestones":len(milestones),"artifact_dir":artifacts.get("artifact_dir"),"evidence_state":"LINKED"}
        append_jsonl(self.runtime/"execution_evidence.jsonl",{"at":now(),**ev})
        result={**ev,"status":"linked"}
        write_json(self.out,result)
        return result
