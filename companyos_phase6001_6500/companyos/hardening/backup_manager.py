from pathlib import Path
from datetime import datetime, timezone
import json

class BackupManager:
    def __init__(self, root):
        self.root=Path(root)
        self.dir=self.root/"backups"/"hardening"
        self.dir.mkdir(parents=True,exist_ok=True)

    def manifest(self, files):
        ts=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        manifest={"timestamp":ts,"files":[str(x) for x in files or []]}
        path=self.dir/f"manifest_{ts}.json"
        path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        return {"manifest":str(path),"count":len(manifest["files"])}
