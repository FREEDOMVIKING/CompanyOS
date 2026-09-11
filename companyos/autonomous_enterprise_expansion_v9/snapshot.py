import shutil, sqlite3
from pathlib import Path
from .util import stamp, now

class SnapshotManager:
    def __init__(self,home,db):
        self.home=Path(home)
        self.db=db
        self.dir=self.home/"backups"/"v9_snapshots"
        self.dir.mkdir(parents=True,exist_ok=True)

    def create(self):
        src=self.db.path
        dest=self.dir/f"companyos_v9_{stamp()}.sqlite3"
        if src.exists():
            s=sqlite3.connect(src)
            d=sqlite3.connect(dest)
            try:
                s.backup(d)
            finally:
                d.close(); s.close()
            info={"status":"snapshot_created","path":str(dest),"created_at":now()}
            self.db.set_kv("last_snapshot",info)
            return info
        return {"status":"no_database"}
