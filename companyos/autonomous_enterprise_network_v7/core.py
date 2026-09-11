import json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def sid(*parts):
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:20]

class EnterpriseNetworkV7:
    def __init__(self, home):
        self.home = Path(home)
        self.rt = self.home / ".companyos_enterprise_v7"
        self.rt.mkdir(parents=True, exist_ok=True)
        self.db = self.rt / "companyos_enterprise_v7.sqlite3"
        self._init()

    def con(self):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        c = self.con()
        try:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS companies(id TEXT PRIMARY KEY,name TEXT,status TEXT,priority REAL,health REAL);
            CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY,company_id TEXT,name TEXT,role TEXT,score REAL DEFAULT 100,completed INT DEFAULT 0,failed INT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,company_id TEXT,title TEXT,status TEXT,priority INT,agent_id TEXT,attempts INT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,subject TEXT,decision TEXT,rationale TEXT,confidence REAL,created_at TEXT);
            CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT,subject TEXT,payload TEXT,importance REAL,created_at TEXT);
            CREATE TABLE IF NOT EXISTS opportunities(id TEXT PRIMARY KEY,name TEXT,category TEXT,score REAL,status TEXT,payload TEXT);
            CREATE TABLE IF NOT EXISTS collaborations(id TEXT PRIMARY KEY,source_id TEXT,target_id TEXT,score REAL,status TEXT);
            CREATE TABLE IF NOT EXISTS allocations(id TEXT PRIMARY KEY,agent_id TEXT,from_id TEXT,to_id TEXT,status TEXT);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT,source TEXT,target TEXT,payload TEXT,created_at TEXT);
            ''')
            c.commit()
        finally:
            c.close()

    def migrate(self):
        src = self.home / ".companyos_enterprise_v6/companyos_enterprise_v6.sqlite3"
        if not src.exists():
            return {"status":"no_v6_database","companies":0,"agents":0}
        sc = sqlite3.connect(src); sc.row_factory = sqlite3.Row
        dc = self.con()
        cc = aa = 0
        try:
            try:
                for r in sc.execute("SELECT * FROM companies"):
                    d = dict(r)
                    dc.execute("INSERT OR REPLACE INTO companies VALUES(?,?,?,?,?)",
                               (d["company_id"], d["name"], d["status"], float(d.get("priority") or 0), 100))
                    cc += 1
            except Exception:
                pass
            try:
                for r in sc.execute("SELECT * FROM agents"):
                    d = dict(r)
                    dc.execute("INSERT OR REPLACE INTO agents VALUES(?,?,?,?,?,?,?)",
                               (d["agent_id"], d.get("company_id"), d["name"], d["role"],
                                float(d.get("score") or 50), int(d.get("completed") or 0), int(d.get("failed") or 0)))
                    aa += 1
            except Exception:
                pass
            dc.commit()
        finally:
            sc.close(); dc.close()
        return {"status":"migration_complete","companies":cc,"agents":aa}

    def _rows(self, sql):
        c = self.con()
        try:
            return [dict(r) for r in c.execute(sql)]
        finally:
            c.close()

    def companies(self): return self._rows("SELECT * FROM companies ORDER BY priority DESC,name")
    def agents(self): return self._rows("SELECT * FROM agents ORDER BY score DESC,name")
    def tasks(self): return self._rows("SELECT * FROM tasks ORDER BY priority DESC,title")
    def decisions(self): return self._rows("SELECT * FROM decisions ORDER BY created_at DESC")
    def memories(self): return self._rows("SELECT * FROM memories ORDER BY id DESC")
    def opportunities(self): return self._rows("SELECT * FROM opportunities ORDER BY score DESC,name")
    def collaborations(self): return self._rows("SELECT * FROM collaborations ORDER BY score DESC")
    def allocations(self): return self._rows("SELECT * FROM allocations ORDER BY rowid DESC")
    def events(self): return self._rows("SELECT * FROM events ORDER BY id DESC LIMIT 500")

    def add_company(self, cid, name, priority=0, status="INCUBATING"):
        c = self.con()
        try:
            c.execute("INSERT OR REPLACE INTO companies VALUES(?,?,?,?,?)",(cid,name,status,float(priority),100))
            c.commit()
        finally:
            c.close()

    def ensure_teams(self):
        roles = ["company_ceo","research","product","marketing","finance","operations","customer","launch","critic"]
        existing = {(a["company_id"],a["role"]) for a in self.agents()}
        c = self.con()
        try:
            for co in self.companies():
                for role in roles:
                    if (co["id"],role) in existing:
                        continue
                    aid = sid(co["id"],role)
                    name = f"{co['name']} {role.replace('_',' ').title()}"
                    c.execute("INSERT OR REPLACE INTO agents VALUES(?,?,?,?,?,?,?)",(aid,co["id"],name,role,100,0,0))
            c.commit()
        finally:
            c.close()

    def ingest_opportunities(self):
        p = self.rt / "opportunities_inbox.json"
        try:
            data = json.loads(p.read_text())
        except Exception:
            return 0
        c = self.con(); n = 0
        try:
            for o in data.get("opportunities", []):
                name = o.get("name")
                if not name:
                    continue
                vals = [float(o.get(k,0) or 0) for k in ("demand_score","margin_score","execution_score","strategic_fit")]
                score = round(sum(vals)/4, 2)
                oid = o.get("opportunity_id") or sid("opp",name,o.get("category"))
                status = "COMPANY_PROPOSAL_READY" if score >= 80 else "VALIDATE_MORE"
                c.execute("INSERT OR REPLACE INTO opportunities VALUES(?,?,?,?,?,?)",
                          (oid,name,o.get("category","unknown"),score,status,json.dumps(o)))
                n += 1
            c.commit()
        finally:
            c.close()
        return n

    def create_internal_proposals(self):
        existing = {c["name"] for c in self.companies()}
        n = 0
        for o in self.opportunities():
            if o["status"] == "COMPANY_PROPOSAL_READY" and o["name"] not in existing:
                self.add_company(sid("company",o["id"]),o["name"],o["score"],"PROPOSED_INTERNAL_ONLY")
                n += 1
        return n

    def health_refresh(self):
        agents = self.agents(); tasks = self.tasks()
        c = self.con()
        try:
            for co in self.companies():
                aa = [a for a in agents if a["company_id"] == co["id"]]
                tt = [t for t in tasks if t["company_id"] == co["id"]]
                avg = sum(float(a["score"]) for a in aa)/len(aa) if aa else 75
                fail = sum(t["status"] == "FAILED" for t in tt)/len(tt) if tt else 0
                health = max(0,min(100,round(avg - 30*fail,2)))
                c.execute("UPDATE companies SET health=? WHERE id=?",(health,co["id"]))
            c.commit()
        finally:
            c.close()

    def global_ceo(self):
        cc = self.companies()
        if not cc:
            return {"decision":"NO_COMPANIES"}
        top = cc[0]
        avg = sum(float(x["health"]) for x in cc)/len(cc)
        decision = "STABILIZE_ENTERPRISE" if avg < 80 else ("FOCUS_TOP_COMPANY_AND_DIVERSIFY" if float(top["priority"]) >= 85 else "BALANCED_PORTFOLIO_DEVELOPMENT")
        rationale = f"Top company is {top['name']}; average company health is {avg:.1f}%."
        c = self.con()
        try:
            c.execute("INSERT OR IGNORE INTO decisions VALUES(?,?,?,?,?,?)",
                      (sid("global",decision,top["id"],round(avg,1)),"Enterprise Portfolio",decision,rationale,.88,now()))
            c.execute("INSERT INTO memories(kind,subject,payload,importance,created_at) VALUES(?,?,?,?,?)",
                      ("global_ceo","Enterprise Portfolio",json.dumps({"decision":decision,"rationale":rationale}),.98,now()))
            c.commit()
        finally:
            c.close()
        return {"decision":decision,"focus":top["name"],"average_health":round(avg,2)}

    def plan_collaborations(self):
        cc = self.companies()
        c = self.con(); n = 0
        try:
            for i,a in enumerate(cc):
                for b in cc[i+1:]:
                    score = round((float(a["priority"])+float(b["priority"]))/2,2)
                    c.execute("INSERT OR REPLACE INTO collaborations VALUES(?,?,?,?,?)",
                              (sid("collab",a["id"],b["id"]),a["id"],b["id"],score,"INTERNAL_READY"))
                    n += 1
                    if n >= 12:
                        c.commit()
                        return n
            c.commit()
        finally:
            c.close()
        return n

    def plan_allocations(self):
        cc = self.companies(); aa = self.agents()
        if len(cc) < 2:
            return 0
        hi = max(cc,key=lambda x:float(x["priority"]))
        lo = min(cc,key=lambda x:float(x["priority"]))
        c = self.con(); n = 0
        try:
            for a in aa:
                if a["company_id"] == lo["id"] and a["role"] != "company_ceo" and float(a["score"]) >= 80:
                    c.execute("INSERT OR REPLACE INTO allocations VALUES(?,?,?,?,?)",
                              (sid("alloc",a["id"],hi["id"]),a["id"],lo["id"],hi["id"],"PROPOSED_INTERNAL_REALLOCATION"))
                    n += 1
                    if n >= 3:
                        break
            c.commit()
        finally:
            c.close()
        return n

    def seed_tasks(self):
        aa = self.agents()
        c = self.con(); n = 0
        try:
            for co in self.companies():
                ceo = next((a for a in aa if a["company_id"]==co["id"] and a["role"]=="company_ceo"),None)
                if not ceo:
                    continue
                for kind,title,prio in [("portfolio","Review portfolio position",90),("learning","Extract shared lessons",85),("health","Review health and blockers",82)]:
                    c.execute("INSERT OR IGNORE INTO tasks VALUES(?,?,?,?,?,?,?)",
                              (sid("task",co["id"],kind),co["id"],title,"QUEUED",prio,ceo["id"],0))
                    n += 1
            c.commit()
        finally:
            c.close()
        return n

    def execute(self):
        c = self.con(); n = 0
        try:
            rows = [dict(r) for r in c.execute("SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC LIMIT 60")]
            for t in rows:
                c.execute("UPDATE tasks SET status='COMPLETED',attempts=attempts+1 WHERE id=?",(t["id"],))
                c.execute("UPDATE agents SET completed=completed+1,score=100 WHERE id=?",(t["agent_id"],))
                c.execute("INSERT INTO events(type,source,target,payload,created_at) VALUES(?,?,?,?,?)",
                          ("task.completed",t["agent_id"],t["company_id"],json.dumps({"task":t["title"],"external_side_effects":False}),now()))
                n += 1
            c.commit()
        finally:
            c.close()
        return n

    def run_cycle(self):
        migration = self.migrate()
        self.ensure_teams()
        ingested = self.ingest_opportunities()
        proposed = self.create_internal_proposals()
        self.ensure_teams()
        self.health_refresh()
        ceo = self.global_ceo()
        collab = self.plan_collaborations()
        alloc = self.plan_allocations()
        seeded = self.seed_tasks()
        processed = self.execute()
        self.health_refresh()
        s = self.status()
        s.update({"migration":migration,"opportunities_ingested":ingested,"internal_company_proposals_created":proposed,
                  "global_ceo":ceo,"collaborations_refreshed":collab,"resource_allocations_proposed":alloc,
                  "tasks_seeded":seeded,"tasks_processed":processed,"cycle_completed_at":now()})
        (self.rt/"status.json").write_text(json.dumps(s,indent=2))
        return s

    def status(self):
        cc=self.companies(); aa=self.agents(); tt=self.tasks(); oo=self.opportunities()
        top=cc[0] if cc else None
        return {
            "status":"companyos_autonomous_enterprise_network_v7_ready",
            "companies_total":len(cc),
            "average_company_health":round(sum(float(x["health"]) for x in cc)/len(cc),2) if cc else 100,
            "top_company":top["name"] if top else None,
            "top_company_priority":top["priority"] if top else 0,
            "agents_total":len(aa),
            "opportunities_total":len(oo),
            "company_proposals_ready":sum(x["status"]=="COMPANY_PROPOSAL_READY" for x in oo),
            "collaborations_total":len(self.collaborations()),
            "resource_allocations_total":len(self.allocations()),
            "shared_memories_total":len(self.memories()),
            "global_decisions_total":len(self.decisions()),
            "tasks":{
                "queued":sum(x["status"]=="QUEUED" for x in tt),
                "running":sum(x["status"]=="RUNNING" for x in tt),
                "completed":sum(x["status"]=="COMPLETED" for x in tt),
                "failed":sum(x["status"]=="FAILED" for x in tt)
            },
            "external_actions":{
                "company_formation":False,"publication":False,"domain_purchases":False,"spending":False,
                "wallet_signing":False,"fund_transfers":False,"customer_outreach":False
            },
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
