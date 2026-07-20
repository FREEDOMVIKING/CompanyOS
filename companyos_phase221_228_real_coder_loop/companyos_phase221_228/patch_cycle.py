from __future__ import annotations
from pathlib import Path

class PatchCycle:
    """223: generation/repair cycle driven by real test feedback."""

    def apply_files(self, workspace, files):
        root=Path(workspace)
        written=[]
        for rel,content in files.items():
            rp=Path(rel)
            if rp.is_absolute() or ".." in rp.parts:
                raise ValueError(f"unsafe path: {rel}")
            dst=root/rp
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_text(str(content),encoding="utf-8")
            written.append(str(rp))
        return written

    def run(self, bridge, verifier, workspace, payload, targeted_test=None, max_attempts=3):
        history=[]
        current_payload=dict(payload)
        for attempt in range(1,max(1,int(max_attempts))+1):
            generated=bridge.invoke(current_payload)
            if not generated.get("success"):
                return {"success":False,"stage":"generation","attempt":attempt,"history":history,"generation":generated}
            written=self.apply_files(workspace,generated["files"])
            verification=verifier.bounded_cycle(workspace,max_attempts=1,targeted_test=targeted_test)
            history.append({"attempt":attempt,"written_files":written,"verification":verification})
            if verification.get("success"):
                return {"success":True,"attempts":attempt,"history":history,"written_files":written}
            current_payload={
                **payload,
                "repair_mode":True,
                "previous_failure":verification,
                "previous_written_files":written,
            }
        return {"success":False,"stage":"verification","attempts":len(history),"history":history}
