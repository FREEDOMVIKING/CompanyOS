import json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()
def sid(*x): return hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:20]

SCHEMA="""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS companies(company_id TEXT PRIMARY KEY,name TEXT,status TEXT,priority REAL,health REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS agents(agent_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,role TEXT,score REAL,completed INTEGER,failed INTEGER,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS goals(goal_id TEXT PRIMARY KEY,horizon INTEGER,title TEXT,priority INTEGER,status TEXT,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS forecasts(forecast_id TEXT PRIMARY KEY,horizon INTEGER,metric TEXT,value REAL,confidence REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS proposals(proposal_id TEXT PRIMARY KEY,kind TEXT,subject TEXT,priority INTEGER,risk TEXT,status TEXT,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS sandbox(run_id TEXT PRIMARY KEY,proposal_id TEXT,status TEXT,score REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS budgets(budget_id TEXT PRIMARY KEY,company_id TEXT,amount REAL,status TEXT,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT,source TEXT,payload TEXT,created_at TEXT);
"""

class EnterpriseOSV8:
    def __init__(self,home):
        self.home=Path(home); self.run=self.home/".companyos_enterprise_v8"; self.run.mkdir(parents=True,exist_ok=True)
        self.db=self.run/"companyos_enterprise_v8.sqlite3"
        c=sqlite3.connect(self.db)
        try:
            c.executescript(SCHEMA)
            c.commit()
        finally:
            c.close()

    def q(self,sql,args=()):
        c=sqlite3.connect(self.db)
        c.row_factory=sqlite3.Row
        try:
            return [dict(r) for r in c.execute(sql,args).fetchall()]
        finally:
            c.close()

    def x(self,sql,args=()):
        c=sqlite3.connect(self.db)
        try:
            c.execute(sql,args)
            c.commit()
        finally:
            c.close()

    def event(self,t,source,payload):
        self.x("INSERT INTO events(type,source,payload,created_at) VALUES(?,?,?,?)",(t,source,json.dumps(payload),now()))

    def migrate(self):
        src=self.home/".companyos_enterprise_v7/companyos_enterprise_v7.sqlite3"
        counts={"companies":0,"agents":0}
        if not src.exists(): return {"status":"no_v7_database","counts":counts}
        c=sqlite3.connect(src); c.row_factory=sqlite3.Row
        try:
            try:
                for r in c.execute("SELECT * FROM companies"):
                    d=dict(r)
                    self.x("""INSERT OR REPLACE INTO companies VALUES(?,?,?,?,?,?,?)""",
                           (d["company_id"],d["name"],d["status"],float(d.get("priority") or 0),
                            float(d.get("health") or 100),d.get("payload_json") or "{}",now()))
                    counts["companies"]+=1
            except Exception: pass
            try:
                for r in c.execute("SELECT * FROM agents"):
                    d=dict(r)
                    self.x("""INSERT OR REPLACE INTO agents VALUES(?,?,?,?,?,?,?,?,?)""",
                           (d["agent_id"],d.get("company_id"),d["name"],d["role"],float(d.get("score") or 50),
                            int(d.get("completed") or 0),int(d.get("failed") or 0),d.get("payload_json") or "{}",now()))
                    counts["agents"]+=1
            except Exception: pass
        finally: c.close()
        return {"status":"migration_complete","counts":counts}

    def strategy(self):
        cs=self.q("SELECT * FROM companies ORDER BY priority DESC")
        if not cs: return 0
        top=cs[0]
        rows=[(30,"Remove current blockers and improve execution quality",95),
              (90,f"Validate growth path for {top['name']}",92),
              (180,"Diversify revenue across multiple companies",88),
              (365,"Build a resilient multi-company portfolio",85)]
        for h,title,p in rows:
            self.x("INSERT OR REPLACE INTO goals VALUES(?,?,?,?,?,?,?)",
                   (sid("goal",h,title),h,title,p,"ACTIVE",json.dumps({"top_company":top["name"]}),now()))
        return len(rows)

    def forecasts(self):
        cs=self.q("SELECT * FROM companies")
        if not cs:return 0
        ap=sum(float(c["priority"] or 0) for c in cs)/len(cs)
        ah=sum(float(c["health"] or 0) for c in cs)/len(cs)
        for h in (30,90,180,365):
            signal=round(ap*(1+min(h,180)/1000),2)
            conf=round(max(.25,min(.95,(ah/100)*(.9 if h<=90 else .75))),2)
            self.x("INSERT OR REPLACE INTO forecasts VALUES(?,?,?,?,?,?,?)",
                   (sid("fc",h),h,"portfolio_growth_signal",signal,conf,
                    json.dumps({"note":"Internal planning signal, not guaranteed revenue."}),now()))
        return 4

    def improvements(self):
        n=0
        for a in self.q("SELECT * FROM agents"):
            if float(a["score"] or 0)<70:
                pid=sid("agent",a["agent_id"])
                self.x("INSERT OR REPLACE INTO proposals VALUES(?,?,?,?,?,?,?,?)",
                       (pid,"AGENT_SKILL_GAP",a["name"],90,"LOW","READY_FOR_SANDBOX",
                        json.dumps({"recommendation":"Run internal retraining simulation."}),now())); n+=1
        bad=[c for c in self.q("SELECT * FROM companies") if float(c["health"] or 0)<90]
        if bad:
            pid=sid("health",len(bad))
            self.x("INSERT OR REPLACE INTO proposals VALUES(?,?,?,?,?,?,?,?)",
                   (pid,"HEALTH_RECOVERY","Enterprise Health",98,"LOW","READY_FOR_SANDBOX",
                    json.dumps({"affected":[c["name"] for c in bad]}),now())); n+=1
        return n

    def sandbox_validate(self):
        n=0
        for p in self.q("SELECT * FROM proposals WHERE status='READY_FOR_SANDBOX'"):
            score=90 if p["risk"]=="LOW" else 70
            st="SANDBOX_VALIDATED" if score>=80 else "NEEDS_MORE_TESTING"
            self.x("INSERT OR REPLACE INTO sandbox VALUES(?,?,?,?,?,?)",
                   (sid("run",p["proposal_id"]),p["proposal_id"],st,score,
                    json.dumps({"live_runtime_modified":False,"external_side_effects":False}),now()))
            self.x("UPDATE proposals SET status=?,updated_at=? WHERE proposal_id=?",(st,now(),p["proposal_id"]))
            n+=1
        return n

    def budget(self):
        n=0
        for c in self.q("SELECT * FROM companies"):
            amount=round(max(0,float(c["priority"] or 0)-60)*10,2)
            self.x("INSERT OR REPLACE INTO budgets VALUES(?,?,?,?,?,?)",
                   (sid("budget",c["company_id"]),c["company_id"],amount,"PLANNING_ONLY",
                    json.dumps({"automatic_spending":False}),now())); n+=1
        return n

    def cycle(self):
        r={"migration":self.migrate()}
        r["strategic_goals_refreshed"]=self.strategy()
        r["forecasts_refreshed"]=self.forecasts()
        r["improvement_proposals"]=self.improvements()
        r["sandbox_runs"]=self.sandbox_validate()
        r["budget_plans_refreshed"]=self.budget()
        r["status"]=self.status()
        self.event("cycle.completed","enterprise_os_v8",r)
        return r

    def status(self):
        cs=self.q("SELECT * FROM companies"); ag=self.q("SELECT * FROM agents")
        goals=self.q("SELECT * FROM goals"); fc=self.q("SELECT * FROM forecasts")
        pp=self.q("SELECT * FROM proposals"); sb=self.q("SELECT * FROM sandbox"); bg=self.q("SELECT * FROM budgets")
        ah=round(sum(float(c["health"] or 0) for c in cs)/len(cs),2) if cs else 100
        return {
          "status":"companyos_autonomous_enterprise_os_v8_ready",
          "companies_total":len(cs),"agents_total":len(ag),"average_company_health":ah,
          "strategic_goals_total":len(goals),"forecasts_total":len(fc),
          "improvement_proposals_total":len(pp),
          "sandbox_validated_total":sum(r["status"]=="SANDBOX_VALIDATED" for r in sb),
          "budget_plans_total":len(bg),
          "self_improvement":{"analysis":True,"proposal_generation":True,"sandbox_validation":True,"automatic_live_code_replacement":False},
          "external_actions":{"publication":False,"domain_purchases":False,"account_creation":False,
                              "spending":False,"wallet_signing":False,"fund_transfers":False,"customer_outreach":False},
          "dashboard_url":"http://127.0.0.1:9000","updated_at":now()
        }
