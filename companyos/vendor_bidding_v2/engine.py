from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class VendorBiddingV2:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"vendor_bidding.json"
    def run(self):
        result={"generated_at":now(),"bids":[{"category":x,"status":"rfq_ready","award":"approval_required"} for x in ["hosting","domain","email","payments"]],"status":"prepared"}
        write_json(self.out,result);return result
