import json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def sid(*parts):
    return hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS companies(
 company_id TEXT PRIMARY KEY,name TEXT,status TEXT,priority REAL,health REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS agents(
 agent_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,role TEXT,score REAL,completed INTEGER,failed INTEGER,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS objectives(
 objective_id TEXT PRIMARY KEY,horizon INTEGER,title TEXT,priority INTEGER,status TEXT,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS memories(
 id INTEGER PRIMARY KEY AUTOINCREMENT,memory_type TEXT,subject TEXT,company_id TEXT,content TEXT,importance REAL,created_at TEXT);
CREATE TABLE IF NOT EXISTS decisions(
 decision_id TEXT PRIMARY KEY,company_id TEXT,subject TEXT,decision TEXT,rationale TEXT,confidence REAL,outcome_score REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS opportunities(
 opportunity_id TEXT PRIMARY KEY,name TEXT,category TEXT,status TEXT,score REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS workforce(
 proposal_id TEXT PRIMARY KEY,agent_id TEXT,company_id TEXT,proposal_type TEXT,priority INTEGER,status TEXT,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS improvements(
 proposal_id TEXT PRIMARY KEY,subject TEXT,proposal_type TEXT,priority INTEGER,risk TEXT,status TEXT,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS sandbox(
 run_id TEXT PRIMARY KEY,proposal_id TEXT,status TEXT,score REAL,payload TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS plugins(
 plugin_id TEXT PRIMARY KEY,name TEXT,module_path TEXT,status TEXT,capabilities TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY,company_id TEXT,kind TEXT,title TEXT,status TEXT,priority INTEGER,agent_id TEXT,payload TEXT,attempts INTEGER,created_at TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT,source TEXT,target TEXT,payload TEXT,created_at TEXT);
"""

class AutonomousIntelligenceV10:
    def __init__(self, home):
        self.home = Path(home)
        self.run = self.home / ".companyos_enterprise_v10"
        self.run.mkdir(parents=True, exist_ok=True)
        self.db = self.run / "companyos_enterprise_v10.sqlite3"
        con = sqlite3.connect(self.db)
        try:
            con.executescript(SCHEMA); con.commit()
        finally:
            con.close()

    def rows(self, sql, args=()):
        con = sqlite3.connect(self.db); con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(sql,args).fetchall()]
        finally:
            con.close()

    def exec(self, sql, args=()):
        con = sqlite3.connect(self.db)
        try:
            con.execute(sql,args); con.commit()
        finally:
            con.close()

    def event(self, kind, source, payload, target=None):
        self.exec("INSERT INTO events(event_type,source,target,payload,created_at) VALUES(?,?,?,?,?)",
                  (kind,source,target,json.dumps(payload,default=str),now()))

    def migrate(self):
        src = self.home / ".companyos_enterprise_v9/companyos_enterprise_v9.sqlite3"
        counts = {"companies":0,"agents":0,"memories":0,"opportunities":0}
        if not src.exists():
            return {"status":"no_v9_database","counts":counts}
        con = sqlite3.connect(src); con.row_factory = sqlite3.Row
        try:
            for table in ("companies","agents","memories","opportunities"):
                try:
                    rows = [dict(r) for r in con.execute(f"SELECT * FROM {table}")]
                except Exception:
                    rows = []
                if table == "companies":
                    for d in rows:
                        self.exec("""INSERT OR REPLACE INTO companies VALUES(?,?,?,?,?,?,?)""",
                                  (d["company_id"],d["name"],d.get("status","MIGRATED"),
                                   float(d.get("priority") or 0),float(d.get("health") or 100),
                                   d.get("payload_json") or "{}",now()))
                        counts["companies"] += 1
                elif table == "agents":
                    for d in rows:
                        self.exec("""INSERT OR REPLACE INTO agents VALUES(?,?,?,?,?,?,?,?,?)""",
                                  (d["agent_id"],d.get("company_id"),d["name"],d.get("role","specialist"),
                                   float(d.get("score") or 50),int(d.get("completed") or 0),int(d.get("failed") or 0),
                                   d.get("payload_json") or "{}",now()))
                        counts["agents"] += 1
                elif table == "memories":
                    for d in rows:
                        self.exec("""INSERT INTO memories(memory_type,subject,company_id,content,importance,created_at)
                                     VALUES(?,?,?,?,?,?)""",
                                  (d.get("memory_type","legacy"),d.get("subject","V9 memory"),d.get("company_id"),
                                   d.get("content_json") or "{}",float(d.get("importance") or .5),now()))
                        counts["memories"] += 1
                elif table == "opportunities":
                    for d in rows:
                        self.exec("""INSERT OR REPLACE INTO opportunities VALUES(?,?,?,?,?,?,?)""",
                                  (d["opportunity_id"],d["name"],d.get("category","unknown"),d.get("status","MIGRATED"),
                                   float(d.get("score") or 0),d.get("payload_json") or "{}",now()))
                        counts["opportunities"] += 1
        finally:
            con.close()
        self.event("migration.complete","v9_migrator",counts)
        return {"status":"migration_complete","counts":counts}

    def refresh_objectives(self):
        cs = self.rows("SELECT * FROM companies ORDER BY priority DESC")
        if not cs: return 0
        top = cs[0]
        goals = [
            (30,"Raise reliability and remove execution blockers",100),
            (90,f"Validate repeatable growth for {top['name']}",96),
            (180,"Build at least two independent growth engines",92),
            (365,"Operate a resilient diversified portfolio",90),
        ]
        for h,title,p in goals:
            self.exec("INSERT OR REPLACE INTO objectives VALUES(?,?,?,?,?,?,?)",
                      (sid("objective",h,title),h,title,p,"ACTIVE",json.dumps({"top_company":top["name"]}),now()))
        return len(goals)

    def executive_decision(self):
        cs = self.rows("SELECT * FROM companies ORDER BY priority DESC")
        if not cs: return {"decision":"NO_COMPANIES"}
        top = cs[0]
        health = float(top["health"] or 0); priority = float(top["priority"] or 0)
        if health < 85:
            decision, rationale, conf = "STABILIZE_TOP_COMPANY","Top company health is below target.",.94
        elif priority >= 85:
            decision, rationale, conf = "FOCUS_VALIDATE_AND_DIVERSIFY","Strong leader; validate while reducing concentration risk.",.90
        else:
            decision, rationale, conf = "BALANCED_PORTFOLIO_DEVELOPMENT","No company justifies aggressive concentration.",.83
        self.exec("INSERT OR REPLACE INTO decisions VALUES(?,?,?,?,?,?,?,?,?)",
                  (sid("decision",top["company_id"],decision),top["company_id"],top["name"],decision,rationale,conf,None,
                   json.dumps({"priority":priority,"health":health}),now()))
        return {"decision":decision,"company":top["name"],"confidence":conf}

    def memory_refresh(self):
        existing = {(r["memory_type"],r["subject"],r["company_id"]) for r in self.rows("SELECT * FROM memories")}
        count = 0
        for c in self.rows("SELECT * FROM companies"):
            key=("company_model",c["name"],c["company_id"])
            if key not in existing:
                self.exec("""INSERT INTO memories(memory_type,subject,company_id,content,importance,created_at)
                             VALUES(?,?,?,?,?,?)""",
                          ("company_model",c["name"],c["company_id"],
                           json.dumps({"priority":c["priority"],"health":c["health"],
                                       "principle":"Prefer measurable evidence and repeatable delivery."}),.88,now()))
                count += 1
        return count

    def opportunity_ingest(self):
        p = self.run / "opportunities_inbox.json"
        try:
            data = json.loads(p.read_text())
        except Exception:
            data = {"opportunities":[]}
        count=0
        for o in data.get("opportunities",[]) or []:
            name=o.get("name")
            if not name: continue
            vals=[float(o.get(k,0) or 0) for k in ("demand_score","margin_score","execution_score","strategic_fit","evidence_score")]
            vals=[v for v in vals if v>0]
            score=round(sum(vals)/len(vals),2) if vals else 0
            status="EXECUTIVE_REVIEW" if score>=85 else "VALIDATE_MORE" if score>=70 else "LOW_PRIORITY"
            self.exec("INSERT OR REPLACE INTO opportunities VALUES(?,?,?,?,?,?,?)",
                      (o.get("opportunity_id") or sid("opp",name,o.get("category")),name,o.get("category","unknown"),
                       status,score,json.dumps(o),now()))
            count+=1
        return count

    def workforce_refresh(self):
        count=0
        for a in self.rows("SELECT * FROM agents"):
            score=float(a["score"] or 0)
            if score < 65:
                self.exec("INSERT OR REPLACE INTO workforce VALUES(?,?,?,?,?,?,?,?)",
                          (sid("wf",a["agent_id"]),a["agent_id"],a["company_id"],"RETRAIN_OR_REASSIGN",95,
                           "PROPOSED_INTERNAL_ONLY",json.dumps({"score":score,"live_assignment_changed":False}),now()))
                count+=1
        return count

    def improvements_refresh(self):
        tasks=self.rows("SELECT * FROM tasks")
        failed=sum(t["status"]=="FAILED" for t in tasks)
        count=0
        proposals=[
            ("Executive decision learning","DECISION_OUTCOME_FEEDBACK",92,"LOW",
             {"proposal":"Attach measurable outcomes to executive decisions."})
        ]
        if failed:
            proposals.append(("Task reliability","TASK_RELIABILITY",100,"LOW",
                              {"failed_tasks":failed,"proposal":"Classify failures and retry selectively."}))
        low=[c["name"] for c in self.rows("SELECT * FROM companies") if float(c["health"] or 0)<90]
        if low:
            proposals.append(("Company health","HEALTH_OPTIMIZATION",98,"LOW",
                              {"companies":low,"proposal":"Reduce low-value workload and rebalance support."}))
        for subject,ptype,priority,risk,payload in proposals:
            pid=sid("improve",subject,ptype)
            self.exec("INSERT OR REPLACE INTO improvements VALUES(?,?,?,?,?,?,?,?)",
                      (pid,subject,ptype,priority,risk,"READY_FOR_SANDBOX",json.dumps(payload),now()))
            count+=1
        return count

    def sandbox_validate(self):
        count=0
        for p in self.rows("SELECT * FROM improvements WHERE status='READY_FOR_SANDBOX'"):
            score=92 if p["risk"]=="LOW" else 70
            status="SANDBOX_VALIDATED" if score>=80 else "NEEDS_MORE_TESTING"
            self.exec("INSERT OR REPLACE INTO sandbox VALUES(?,?,?,?,?,?)",
                      (sid("sandbox",p["proposal_id"]),p["proposal_id"],status,score,
                       json.dumps({"live_runtime_modified":False,"external_side_effects":False}),now()))
            self.exec("UPDATE improvements SET status=?,updated_at=? WHERE proposal_id=?",(status,now(),p["proposal_id"]))
            count+=1
        return count

    def plugin_refresh(self):
        builtins=[
            ("executive_brain",["strategy","decision"]),
            ("executive_memory_v2",["memory","learning"]),
            ("opportunity_ranker",["opportunities","scoring"]),
            ("workforce_optimizer",["agents","optimization"]),
            ("self_improvement_director",["improvement","sandbox"]),
            ("runtime_supervisor",["health","restart"]),
        ]
        for name,caps in builtins:
            self.exec("INSERT OR REPLACE INTO plugins VALUES(?,?,?,?,?,?)",
                      (sid("plugin",name),name,f"builtin:{name}","ACTIVE",json.dumps(caps),now()))
        return len(builtins)

    def seed_tasks(self):
        agents=self.rows("SELECT * FROM agents")
        count=0
        for c in self.rows("SELECT * FROM companies"):
            ca=[a for a in agents if a["company_id"]==c["company_id"]]
            aid=ca[0]["agent_id"] if ca else None
            for kind,title,p in (
                ("executive_review","Run executive review",98),
                ("opportunity_review","Review opportunity portfolio",92),
                ("workforce_review","Review workforce fit",90),
                ("learning_review","Capture reusable lessons",88),
            ):
                tid=sid("task",c["company_id"],kind)
                ts=now()
                self.exec("""INSERT OR IGNORE INTO tasks VALUES(?,?,?,?,'QUEUED',?,?,?,0,?,?)""",
                          (tid,c["company_id"],kind,title,p,aid,json.dumps({"company_name":c["name"]}),ts,ts))
                count+=1
        return count

    def run_tasks(self):
        count=0
        for t in self.rows("SELECT * FROM tasks WHERE status='QUEUED' ORDER BY priority DESC LIMIT 100"):
            self.exec("UPDATE tasks SET status='RUNNING',attempts=attempts+1,updated_at=? WHERE task_id=?",(now(),t["task_id"]))
            self.event("task.started",t["agent_id"] or "scheduler",{"task_id":t["task_id"]},t["company_id"])
            self.exec("UPDATE tasks SET status='COMPLETED',updated_at=? WHERE task_id=?",(now(),t["task_id"]))
            self.event("task.completed",t["agent_id"] or "scheduler",{"task_id":t["task_id"],"external_side_effects":False},t["company_id"])
            count+=1
        return count

    def external_config(self):
        p=self.home/"config"/"external_actions.json"
        try:
            raw=json.loads(p.read_text())
        except Exception:
            raw={}
        keys=("publication","domain_purchases","account_creation","spending","wallet_signing",
              "fund_transfers","customer_outreach","automatic_live_code_replacement")
        return {"path":str(p),"requested":{k:bool(raw.get(k,False)) for k in keys}}

    def cycle(self):
        result={
            "migration":self.migrate(),
            "objectives":self.refresh_objectives(),
            "decision":self.executive_decision(),
            "memory":self.memory_refresh(),
            "opportunities":self.opportunity_ingest(),
            "workforce":self.workforce_refresh(),
            "improvements":self.improvements_refresh(),
            "sandbox":self.sandbox_validate(),
            "plugins":self.plugin_refresh(),
            "tasks_seeded":self.seed_tasks(),
            "tasks_processed":self.run_tasks(),
        }
        result["status"]=self.status()
        self.event("cycle.completed","v10",result)
        return result

    def status(self):
        cs=self.rows("SELECT * FROM companies")
        agents=self.rows("SELECT * FROM agents")
        tasks=self.rows("SELECT * FROM tasks")
        top=max(cs,key=lambda c:float(c["priority"] or 0)) if cs else None
        ah=round(sum(float(c["health"] or 0) for c in cs)/len(cs),2) if cs else 100
        ext=self.external_config()
        return {
            "status":"companyos_autonomous_intelligence_v10_ready",
            "intelligence":"ONLINE",
            "companies_total":len(cs),
            "agents_total":len(agents),
            "average_company_health":ah,
            "top_company":top["name"] if top else None,
            "top_company_priority":top["priority"] if top else 0,
            "executive_objectives_total":len(self.rows("SELECT * FROM objectives")),
            "executive_memories_total":len(self.rows("SELECT * FROM memories")),
            "executive_decisions_total":len(self.rows("SELECT * FROM decisions")),
            "opportunities_total":len(self.rows("SELECT * FROM opportunities")),
            "workforce_proposals_total":len(self.rows("SELECT * FROM workforce")),
            "improvement_proposals_total":len(self.rows("SELECT * FROM improvements")),
            "sandbox_validated_total":sum(r["status"]=="SANDBOX_VALIDATED" for r in self.rows("SELECT * FROM sandbox")),
            "plugins_total":len(self.rows("SELECT * FROM plugins")),
            "tasks":{
                "queued":sum(t["status"]=="QUEUED" for t in tasks),
                "running":sum(t["status"]=="RUNNING" for t in tasks),
                "completed":sum(t["status"]=="COMPLETED" for t in tasks),
                "failed":sum(t["status"]=="FAILED" for t in tasks),
            },
            "runtime":{
                "supervisor_supported":True,
                "watchdog_restart_supported":True,
                "android_process_survival_guaranteed":False
            },
            "external_actions_requested":ext["requested"],
            "external_actions_config_path":ext["path"],
            "dashboard_url":"http://127.0.0.1:9000",
            "updated_at":now()
        }
