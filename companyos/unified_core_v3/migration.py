import sqlite3, json
from pathlib import Path
from .util import read_json, stable_id, now

class Migrator:
    def __init__(self, home, db):
        self.home=Path(home)
        self.live=self.home/".companyos_runtime"
        self.v2=self.home/".companyos_unified_v2/companyos_unified_v2.sqlite3"
        self.db=db

    def import_v2(self):
        counts={"modules":0,"ventures":0}
        if not self.v2.exists():
            return counts
        try:
            c=sqlite3.connect(self.v2)
            c.row_factory=sqlite3.Row
            try:
                for r in c.execute("SELECT * FROM modules"):
                    d=dict(r)
                    payload=json.loads(d.get("payload_json") or "{}")
                    self.db.upsert_module(d["module_id"],d["name"],d.get("source"),d.get("status"),bool(d.get("healthy")),payload)
                    counts["modules"]+=1
                for r in c.execute("SELECT * FROM ventures"):
                    d=dict(r)
                    payload=json.loads(d.get("payload_json") or "{}")
                    self.db.upsert_venture(d["venture_id"],d["name"],d.get("stage"),d.get("score",0),d.get("source"),payload)
                    counts["ventures"]+=1
            finally:
                c.close()
        except Exception as e:
            self.db.event("migration.v2_error","migrator",{"error":str(e)})
        return counts

    def import_legacy_live(self):
        n=0
        if not self.live.exists(): return 0
        for p in self.live.glob("*.json"):
            d=read_json(p,{})
            if not isinstance(d,dict): continue
            status=str(d.get("status") or d.get("state") or "unknown")
            healthy=not any(x in status.lower() for x in ("fail","error","stopped","down"))
            self.db.upsert_module(stable_id("legacy",p.name),p.stem,str(p),status,healthy,d)
            n+=1
        return n

    def run(self):
        v2=self.import_v2()
        legacy=self.import_legacy_live()
        report={"status":"migration_complete","v2":v2,"legacy_modules":legacy,"updated_at":now()}
        self.db.set_kv("migration_report",report)
        self.db.event("migration.complete","migrator",report)
        return report
