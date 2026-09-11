from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class ProposalContractsV2:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"proposal_contracts.json"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{});title=latest.get("title","CompanyOS Venture")
        folder=self.home/"generated_proposals";folder.mkdir(parents=True,exist_ok=True);file=folder/("proposal-"+str(abs(hash(title)))+".json")
        write_json(file,{"title":title+" Proposal","legal_status":"draft_requires_review","generated_at":now()})
        result={"generated_at":now(),"proposal_file":str(file),"status":"drafted"}
        write_json(self.out,result);return result
