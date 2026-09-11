import sqlite3, json
from pathlib import Path
from .util import stable_id, read_json, now

class Migrator:
    def __init__(self,home,db):
        self.home=Path(home); self.db=db
        self.v3=self.home/".companyos_unified_v3/companyos_unified_v3.sqlite3"
        self.live=self.home/".companyos_runtime"

    def import_v3(self):
        out={"modules":0,"ventures":0,"agents":0,"plugins":0}
        if not self.v3.exists(): return out
        try:
            c=sqlite3.connect(self.v3); c.row_factory=sqlite3.Row
            try:
                for table in ("modules","ventures","agents","plugins"):
                    try: rows=c.execute(f"SELECT * FROM {table}").fetchall()
                    except Exception: rows=[]
                    for r in rows:
                        d=dict(r)
                        if table=="modules":
                            self.db.upsert_module(d["module_id"],d["name"],d.get("source"),d.get("status"),bool(d.get("healthy")),json.loads(d.get("payload_json") or "{}"))
                        elif table=="ventures":
                            self.db.upsert_venture(d["venture_id"],d["name"],d.get("stage"),d.get("score"),d.get("source"),json.loads(d.get("payload_json") or "{}"))
                        elif table=="agents":
                            self.db.upsert_agent(d["agent_id"],d["name"],d["role"],bool(d.get("enabled")))
                        elif table=="plugins":
                            self.db.upsert_plugin(d["plugin_id"],d["name"],d["version"],d.get("source"),json.loads(d.get("capabilities_json") or "[]"),bool(d.get("enabled")),d.get("health") or "UNKNOWN")
                        out[table]+=1
            finally:
                c.close()
        except Exception as e:
            self.db.event("migration.v3_error","migrator",{"error":str(e)})
        return out

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
        r={"status":"migration_complete","v3":self.import_v3(),"legacy_modules":self.import_legacy(),"updated_at":now()}
        self.db.set_kv("migration_report",r); self.db.event("migration.complete","migrator",r)
        return r
