from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class ExecutiveAnalyticsV3:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"executive_analytics.json"
    def run(self):
        root=self.home/"companyos_runtime"/"execution_suite_60001_70000";names=["product_factory","task_delegation","crm_automation","proposal_contracts","vendor_bidding","acquisition_scanner","revenue_optimizer_v4","qa_recovery"]
        result={"phase":"60001-70000","generated_at":now(),"modules":{n:read_json(root/(n+".json"),{}) for n in names},"status":"active"}
        write_json(self.out,result);return result
