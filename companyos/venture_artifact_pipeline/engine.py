from pathlib import Path
from companyos.runtime_common_v3 import read_json,write_json,append_jsonl,now
class VentureArtifactPipeline:
    def __init__(self,home):
        self.home=Path(home)
        self.runtime=self.home/"companyos_runtime"/"roadmap_execution_70001_80000"
        self.out=self.runtime/"artifacts.json"
    def run(self):
        execution=read_json(self.runtime/"active_execution.json",{}).get("execution",{})
        subject=execution.get("subject","venture")
        slug="".join(c.lower() if c.isalnum() else "-" for c in subject).strip("-") or "venture"
        folder=self.home/"generated_ventures"/slug;folder.mkdir(parents=True,exist_ok=True)
        (folder/"README.md").write_text("# "+subject+"\n",encoding="utf-8")
        (folder/"offer.md").write_text("Draft offer for "+subject+".\n",encoding="utf-8")
        (folder/"launch_checklist.md").write_text("- [ ] Validate demand\n- [ ] Finish MVP\n- [ ] Prepare launch\n",encoding="utf-8")
        result={"subject":subject,"artifact_dir":str(folder),"files":["README.md","offer.md","launch_checklist.md"],"status":"generated"}
        write_json(self.out,result)
        return result
