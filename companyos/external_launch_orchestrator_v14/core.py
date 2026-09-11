import json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()
def sid(*x): return hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]

SCHEMA="""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS company_builds(build_id TEXT PRIMARY KEY,launch_id TEXT,company_id TEXT,company_name TEXT,status TEXT,workspace_path TEXT,website_path TEXT,product_path TEXT,marketing_path TEXT,support_path TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS products(product_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,product_type TEXT,status TEXT,price_hint REAL,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS campaigns(campaign_id TEXT PRIMARY KEY,company_id TEXT,name TEXT,channel TEXT,status TEXT,message TEXT,payload_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS readiness(company_id TEXT PRIMARY KEY,company_name TEXT,score REAL,status TEXT,blockers_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS manifests(company_id TEXT PRIMARY KEY,status TEXT,manifest_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS domains(id TEXT PRIMARY KEY,company_id TEXT,candidate TEXT,status TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS dns(company_id TEXT PRIMARY KEY,status TEXT,records_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS storefronts(company_id TEXT PRIMARY KEY,status TEXT,catalog_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS acquisition(company_id TEXT PRIMARY KEY,status TEXT,plan_json TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS connectors(name TEXT PRIMARY KEY,category TEXT,status TEXT,required INTEGER,updated_at TEXT);
CREATE TABLE IF NOT EXISTS action_queue(id TEXT PRIMARY KEY,company_id TEXT,action_type TEXT,status TEXT,risk TEXT,connector TEXT,description TEXT,updated_at TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,company_id TEXT,event_type TEXT,decision TEXT,payload_json TEXT,created_at TEXT);
"""

class ExternalLaunchOrchestratorV14:
    def __init__(self,home):
        self.home=Path(home); self.run=self.home/".companyos_enterprise_v14"
        self.run.mkdir(parents=True,exist_ok=True); self.db=self.run/"companyos_enterprise_v14.sqlite3"
        c=sqlite3.connect(self.db); c.executescript(SCHEMA); c.commit(); c.close()

    def rows(self,sql,args=()):
        c=sqlite3.connect(self.db); c.row_factory=sqlite3.Row
        try: return [dict(r) for r in c.execute(sql,args).fetchall()]
        finally: c.close()

    def exec(self,sql,args=()):
        c=sqlite3.connect(self.db)
        try: c.execute(sql,args); c.commit()
        finally: c.close()

    def migrate(self):
        src=self.home/".companyos_enterprise_v13/companyos_enterprise_v13.sqlite3"
        counts={"company_builds":0,"products":0,"campaigns":0}
        if not src.exists(): return {"status":"no_v13_database","counts":counts}
        c=sqlite3.connect(src); c.row_factory=sqlite3.Row
        try:
            for table in ("company_builds","products","campaigns"):
                try: rows=[dict(r) for r in c.execute(f"SELECT * FROM {table}")]
                except Exception: rows=[]
                for d in rows:
                    if table=="company_builds":
                        self.exec("INSERT OR REPLACE INTO company_builds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                          (d["build_id"],d["launch_id"],d["company_id"],d["company_name"],d["status"],d["workspace_path"],d["website_path"],d["product_path"],d["marketing_path"],d["support_path"],d.get("payload_json") or "{}",now()))
                    elif table=="products":
                        self.exec("INSERT OR REPLACE INTO products VALUES(?,?,?,?,?,?,?,?)",
                          (d["product_id"],d["company_id"],d["name"],d["product_type"],d["status"],float(d.get("price_hint") or 0),d.get("payload_json") or "{}",now()))
                    else:
                        self.exec("INSERT OR REPLACE INTO campaigns VALUES(?,?,?,?,?,?,?,?)",
                          (d["campaign_id"],d["company_id"],d["name"],d["channel"],d["status"],d["message"],d.get("payload_json") or "{}",now()))
                    counts[table]+=1
        finally: c.close()
        return {"status":"migration_complete","counts":counts}

    def cycle(self):
        self.migrate()
        for n,cat,req in [("static_host","hosting",1),("domain_registrar","domain",1),("dns_provider","dns",1),("storefront","commerce",0),("email_outreach","marketing",0),("analytics","analytics",0),("payment_processor","payments",0)]:
            self.exec("INSERT OR REPLACE INTO connectors VALUES(?,?,?,?,?)",(n,cat,"NOT_CONFIGURED",req,now()))
        products={x["company_id"]:x for x in self.rows("SELECT * FROM products")}
        campaigns={x["company_id"]:x for x in self.rows("SELECT * FROM campaigns")}
        for b in self.rows("SELECT * FROM company_builds"):
            checks=[Path(b[k]).exists() for k in ("workspace_path","website_path","product_path","marketing_path","support_path")]
            score=round(sum(checks)/5*100,2); blockers=[k for k,v in zip(("workspace","website","product","marketing","support"),checks) if not v]
            status="LAUNCH_PACKAGE_READY" if score>=80 else "NEEDS_REPAIR"
            self.exec("INSERT OR REPLACE INTO readiness VALUES(?,?,?,?,?,?)",(b["company_id"],b["company_name"],score,status,json.dumps(blockers),now()))
            self.exec("INSERT INTO audit(company_id,event_type,decision,payload_json,created_at) VALUES(?,?,?,?,?)",(b["company_id"],"launch.readiness",status,json.dumps({"score":score,"blockers":blockers}),now()))
            if status!="LAUNCH_PACKAGE_READY": continue
            manifest={"source_path":b["website_path"],"target":"static_web_host","publish_mode":"REVIEW_REQUIRED","external_publish":False}
            self.exec("INSERT OR REPLACE INTO manifests VALUES(?,?,?,?)",(b["company_id"],"READY_FOR_REVIEW",json.dumps(manifest),now()))
            slug="".join(ch for ch in b["company_name"].lower() if ch.isalnum()) or "venture"
            for i,d in enumerate((f"{slug}.com",f"get{slug}.com",f"{slug}hq.com")):
                self.exec("INSERT OR REPLACE INTO domains VALUES(?,?,?,?,?)",(sid("domain",b["company_id"],d),b["company_id"],d,"SUGGESTED_ONLY",now()))
            self.exec("INSERT OR REPLACE INTO dns VALUES(?,?,?,?)",(b["company_id"],"PLAN_READY",json.dumps([{"type":"A","name":"@","value":"<host-target>"},{"type":"CNAME","name":"www","value":"<host-name>"}]),now()))
            p=products.get(b["company_id"])
            if p:
                self.exec("INSERT OR REPLACE INTO storefronts VALUES(?,?,?,?)",(b["company_id"],"PLAN_READY",json.dumps([{"name":p["name"],"price_hint":p["price_hint"],"checkout":"DISABLED"}]),now()))
            c=campaigns.get(b["company_id"])
            self.exec("INSERT OR REPLACE INTO acquisition VALUES(?,?,?,?)",(b["company_id"],"PLAN_READY",json.dumps({"channels":["email","social","direct_outreach"],"message":c["message"] if c else f"Introducing {b['company_name']}","automatic_outreach":False}),now()))
            for typ,risk,connector,desc in [
                ("PUBLISH_STATIC_SITE","HIGH","static_host","Publish generated website."),
                ("PURCHASE_DOMAIN","HIGH","domain_registrar","Purchase selected domain."),
                ("APPLY_DNS","MEDIUM","dns_provider","Apply DNS records."),
                ("CREATE_STOREFRONT","MEDIUM","storefront","Create external storefront."),
                ("START_OUTREACH","MEDIUM","email_outreach","Begin acquisition outreach.")]:
                self.exec("INSERT OR REPLACE INTO action_queue VALUES(?,?,?,?,?,?,?,?)",(sid("action",b["company_id"],typ),b["company_id"],typ,"REVIEW_REQUIRED",risk,connector,desc,now()))
        return {"status":self.status()}

    def status(self):
        ready=self.rows("SELECT * FROM readiness"); actions=self.rows("SELECT * FROM action_queue"); conns=self.rows("SELECT * FROM connectors")
        return {
          "status":"companyos_external_launch_orchestrator_v14_ready",
          "external_launch_orchestrator":"ONLINE",
          "company_builds_total":len(self.rows("SELECT * FROM company_builds")),
          "launch_ready_total":sum(x["status"]=="LAUNCH_PACKAGE_READY" for x in ready),
          "deployment_manifests_total":len(self.rows("SELECT * FROM manifests")),
          "domain_suggestions_total":len(self.rows("SELECT * FROM domains")),
          "dns_plans_total":len(self.rows("SELECT * FROM dns")),
          "storefront_plans_total":len(self.rows("SELECT * FROM storefronts")),
          "acquisition_plans_total":len(self.rows("SELECT * FROM acquisition")),
          "external_actions_review_required":sum(x["status"]=="REVIEW_REQUIRED" for x in actions),
          "connectors_total":len(conns),
          "connectors_configured":sum(x["status"]=="CONFIGURED" for x in conns),
          "automatic_external_publish":False,"automatic_domain_purchase":False,
          "automatic_account_creation":False,"automatic_spending":False,
          "automatic_wallet_signing":False,"automatic_fund_transfers":False,
          "automatic_customer_outreach":False,
          "dashboard_url":"http://127.0.0.1:9000","updated_at":now()
        }
