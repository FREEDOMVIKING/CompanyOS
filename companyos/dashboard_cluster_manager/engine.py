from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class DashboardClusterManager:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"dashboard_cluster.json"
    def run(self):
        result={"ports":{"master_control":8766,"venture_progress":8767,"activity_ledger":8768},"launcher":str(self.home/"dashboard_cluster.sh"),"status":"configured"}
        write_json(self.out,result)
        return result
