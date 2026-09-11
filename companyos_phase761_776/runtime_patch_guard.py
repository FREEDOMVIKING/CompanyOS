from pathlib import Path
class RuntimePatchGuard:
    """773: locate patch targets and prevent blind source edits."""
    def locate(self,root):
        root=Path(root)
        candidates=[
            root/"src"/"companyos_phase705_720"/"closed_loop_cycle.py",
            root/"companyos_phase705_720"/"closed_loop_cycle.py",
        ]
        target=next((p for p in candidates if p.exists()),None)
        return {"found":target is not None,"path":str(target) if target else None}
