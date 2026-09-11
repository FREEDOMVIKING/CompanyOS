from pathlib import Path
from companyos.runtime_common_v2 import read_json,write_json,now
class ProductFactoryV2:
    def __init__(self,home):
        self.home=Path(home);self.out=self.home/"companyos_runtime"/"execution_suite_60001_70000"/"product_factory.json"
    def run(self):
        latest=read_json(self.home/"companyos_runtime"/"venture_builder"/"latest_build.json",{})
        title=latest.get("title","CompanyOS Venture")
        folder=self.home/"generated_products"/("".join(c.lower() if c.isalnum() else "-" for c in title).strip("-") or "venture")
        folder.mkdir(parents=True,exist_ok=True);(folder/"README.md").write_text("# "+title+"\n")
        result={"phase":"60001-70000","generated_at":now(),"venture":title,"product_dir":str(folder),"status":"generated"}
        write_json(self.out,result);return result
