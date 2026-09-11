from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class QARecoveryV2:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"qa_recovery.json"
    def run(self):
        logs=list((self.home/"logs").glob("*.log")) if (self.home/"logs").exists() else []
        result={"generated_at":now(),"log_count":len(logs),"empty_log_count":sum(1 for x in logs if x.stat().st_size==0),"status":"active"}
        write_json(self.out,result);return result
