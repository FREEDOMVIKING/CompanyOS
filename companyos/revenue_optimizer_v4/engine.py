from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class RevenueOptimizerV4:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"revenue_optimizer_v4.json"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{});base=latest.get("components",{}).get("revenue",{}).get("baseline",{})
        rev=float(base.get("monthly_revenue",0) or 0);profit=float(base.get("monthly_profit",0) or 0);margin=profit/rev if rev else 0
        result={"generated_at":now(),"baseline":{"revenue":rev,"profit":profit,"margin":round(margin,4)},"actions":["validate pricing","improve margin","scale best channel"],"status":"optimized"}
        write_json(self.out,result);return result
