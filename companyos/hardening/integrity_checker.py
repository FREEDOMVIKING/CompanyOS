import hashlib
from pathlib import Path

class IntegrityChecker:
    def hash_file(self, path):
        p=Path(path)
        if not p.exists() or not p.is_file():
            return {"path":str(p),"exists":False,"sha256":None}
        h=hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda:f.read(65536),b""):
                h.update(chunk)
        return {"path":str(p),"exists":True,"sha256":h.hexdigest()}

    def verify_required(self, paths):
        rows=[self.hash_file(p) for p in paths or []]
        return {"ok":all(r["exists"] for r in rows),"files":rows}
