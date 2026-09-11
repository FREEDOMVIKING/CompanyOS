import sqlite3, json
from pathlib import Path
from .util import stable_id, read_json, now

class Migrator:
    def __init__(self,home,db):
        self.home=Path(home); self.db=db
        self.v4=self.home/".companyos_unified_v4/companyos_unified_v4.sqlite3"
        self.live=self.home/".companyos_runtime"

    def import_v4(self):
        counts={"modules":0,"ventures":0,"agents":0,"plugins":0}
        if not self.v4.exists(): return counts
        try:
            c=sqlite3.connect(self.v4); c.row_factory=sqlite3.Row
            try:
                for r in c.execute("SELECT * FROM modules"):
                    d=dict(r); self.db.upsert_module(d["module_id"],d["name"],d.get("source"),d.get("status"),
                        bool(d.get("healthy")),json.loads(d.get("payload_json") or "{}")); counts["modules"]+=1
                for r in c.execute("SELECT * FROM ventures"):
                    d=dict(r); self.db.upsert_venture(d["venture_id"],d["name"],d.get("stage"),d.get("score"),
                        d.get("source"),json.loads(d.get("payload_json") or "{}")); counts["ventures"]+=1
                for r in c.execute("SELECT * FROM agents"):
                    d=dict(r); self.db.upsert_agent(d["agent_id"],d["name"],d["role"],bool(d.get("enabled"))); counts["agents"]+=1
                for r in c.execute("SELECT * FROM plugins"):
                    d=dict(r); self.db.upsert_plugin(d["plugin_id"],d["name"],d["version"],d.get("source"),None,
                        json.loads(d.get("capabilities_json") or "[]"),bool(d.get("enabled")),d.get("health") or "UNKNOWN"); counts["plugins"]+=1
            finally:
                c.close()
        except Exception as e:
            self.db.event("migration.v4_error","migrator",{"error":str(e)})
        return counts

    def import_legacy(self):
        n=0
        if not self.live.exists(): return n
        for p in self.live.glob("*.json"):
            d=read_json(p,{})
            if not isinstance(d,dict): continue
            status=str(d.get("status") or d.get("state") or "unknown")
            healthy=not any(x in status.lower() for x in ("fail","error","stopped","down"))
            self.db.upsert_module(stable_id("legacy",p.name),p.stem,str(p),status,healthy,d)
            n+=1
        return n

    def run(self):
        report={"status":"migration_complete","v4":self.import_v4(),"legacy_modules":self.import_legacy(),"updated_at":now()}
        self.db.set_kv("migration_report",report)
        self.db.event("migration.complete","migrator",report)
        return report
