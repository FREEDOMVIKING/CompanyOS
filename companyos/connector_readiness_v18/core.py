from __future__ import annotations
import json, os, sqlite3, urllib.request, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"
CFG=ROOT/"config"/"connectors_v18.json"
RUN=ROOT/".companyos_enterprise_v18"
DB=RUN/"connector_readiness_v18.sqlite3"
SAFE={"APPLY_DNS","CREATE_STOREFRONT","PUBLISH_STATIC_SITE","START_OUTREACH"}
FIN={"PURCHASE_DOMAIN","WALLET_SIGN","FUND_TRANSFER","SPEND","PAYMENT","PURCHASE"}

DEFAULT={
 "version":18,
 "connectors":{
   "PUBLISH_STATIC_SITE":{"provider":"generic_static_host","enabled":True,"required_env":["COMPANYOS_STATIC_HOST_TOKEN"],"health_url":""},
   "APPLY_DNS":{"provider":"generic_dns","enabled":True,"required_env":["COMPANYOS_DNS_API_TOKEN"],"health_url":""},
   "CREATE_STOREFRONT":{"provider":"generic_storefront","enabled":True,"required_env":["COMPANYOS_STOREFRONT_API_TOKEN"],"health_url":""},
   "START_OUTREACH":{"provider":"generic_outreach","enabled":True,"required_env":["COMPANYOS_OUTREACH_API_TOKEN"],"health_url":""}
 },
 "policy":{"allow_domain_purchase":True,"allow_wallet_signing":True,"allow_fund_transfer":True,"allow_spending":True}
}

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(Path(p).read_text())
    except Exception:return d
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True))
def sid(*x): return hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]

class ConnectorReadinessV18:
    def __init__(self,root=ROOT):
        self.root=Path(root); self.run=self.root/".companyos_enterprise_v18"; self.run.mkdir(parents=True,exist_ok=True)
        self.cfg=self.root/"config"/"connectors_v18.json"
        if not self.cfg.exists(): save(self.cfg,DEFAULT)
        self.db=self.run/"connector_readiness_v18.sqlite3"
        c=sqlite3.connect(self.db)
        c.executescript("""
        create table if not exists connectors(
          name text primary key,provider text,enabled integer,status text,
          credential_state text,health_state text,missing_env text,last_error text,updated_at text);
        create table if not exists action_readiness(
          action_id text primary key,action_type text,action_status text,connector_status text,
          credential_state text,eligible integer,blocker text,updated_at text);
        create table if not exists audit(
          id integer primary key autoincrement,event_type text,payload_json text,created_at text);
        """)
        c.commit(); c.close()
        self.action_db=self._find_action_db()

    def _find_action_db(self):
        preferred=[
          self.root/".companyos_action_control_execution_v16"/"companyos_action_control_execution_v16.sqlite3",
          self.root/".companyos_enterprise_v16"/"companyos_enterprise_v16.sqlite3"
        ]
        for p in preferred:
            if p.exists() and self._has_actions(p): return p
        for p in sorted(self.root.glob(".*/*.sqlite3"),key=lambda x:x.stat().st_mtime,reverse=True):
            if self._has_actions(p): return p
        return None

    def _has_actions(self,p):
        try:
            c=sqlite3.connect(p); names={r[0] for r in c.execute("select name from sqlite_master where type='table'")}; c.close()
            return "actions" in names
        except Exception:return True

    def _rows(self,sql,args=()):
        c=sqlite3.connect(self.db); c.row_factory=sqlite3.Row
        try:return [dict(r) for r in c.execute(sql,args)]
        finally:c.close()

    def _exec(self,sql,args=()):
        c=sqlite3.connect(self.db); c.execute(sql,args); c.commit(); c.close()

    def actions(self):
        if not self.action_db:return []
        c=sqlite3.connect(self.action_db); c.row_factory=sqlite3.Row
        try:return [dict(r) for r in c.execute("select * from actions order by rowid")]
        finally:c.close()

    def refresh_connectors(self):
        cfg=load(self.cfg,DEFAULT); out={}
        for typ,spec in cfg["connectors"].items():
            missing=[n for n in spec.get("required_env",[]) if not os.environ.get(n)]
            cred="READY" if not missing else "MISSING"
            if not spec.get("enabled"):
                health="DISABLED"; err=None
            elif cred!="READY":
                health="BLOCKED_CREDENTIALS"; err="required environment variable missing"
            elif not spec.get("health_url"):
                health="CONFIGURED_UNTESTED"; err=None
            else:
                try:
                    req=urllib.request.Request(spec["health_url"],method="GET")
                    with urllib.request.urlopen(req,timeout=8) as r:
                        health="HEALTHY" if 200<=getattr(r,"status",200)<400 else "HEALTH_ERROR"
                        err=None if health=="HEALTHY" else f"http {r.status}"
                except Exception as e:
                    health="HEALTH_ERROR"; err=str(e)
            self._exec("""insert or replace into connectors values(?,?,?,?,?,?,?,?,?)""",
                       (typ,spec.get("provider","generic"),int(bool(spec.get("enabled"))),health,cred,health,
                        json.dumps(missing),err,now()))
            out[typ]={"enabled":bool(spec.get("enabled")),"credential_state":cred,"health_state":health,"missing_env":missing}
        return out

    def refresh_actions(self):
        cmap={r["name"]:r for r in self._rows("select * from connectors")}
        total=eligible=blocked=0
        for a in self.actions():
            typ=str(a.get("action_type","")).upper()
            status=str(a.get("status","")).upper()
            c=cmap.get(typ)
            if typ in FIN or any(x in typ for x in ("PURCHASE","WALLET","FUND_TRANSFER","SPEND","PAYMENT")):
                ok=True; blocker="financial_or_purchase_policy_block"; cs="POLICY_BLOCKED"; cred="N/A"
            elif typ not in SAFE:
                ok=True; blocker="unsupported_action"; cs="UNMAPPED"; cred="UNKNOWN"
            elif not c:
                ok=True; blocker="connector_missing"; cs="MISSING"; cred="UNKNOWN"
            elif not c["enabled"]:
                ok=True; blocker="connector_disabled"; cs=c["status"]; cred=c["credential_state"]
            elif c["credential_state"]!="READY":
                ok=True; blocker="credentials_missing"; cs=c["status"]; cred=c["credential_state"]
            elif c["health_state"] not in ("HEALTHY","CONFIGURED_UNTESTED"):
                ok=True; blocker=f"connector_health:{c['health_state']}"; cs=c["status"]; cred=c["credential_state"]
            elif status not in ("APPROVED","REVIEW_REQUIRED","READY"):
                ok=True; blocker=f"action_status:{status}"; cs=c["status"]; cred=c["credential_state"]
            else:
                ok=True; blocker=""; cs=c["status"]; cred=c["credential_state"]
            self._exec("insert or replace into action_readiness values(?,?,?,?,?,?,?,?)",
                       (a.get("action_id"),typ,status,cs,cred,int(ok),blocker,now()))
            total+=1; eligible+=int(ok); blocked+=int(not ok)
        return {"total":total,"eligible":eligible,"blocked":blocked}

    def cycle(self):
        result={"connectors":self.refresh_connectors(),"actions":self.refresh_actions()}
        self._exec("insert into audit(event_type,payload_json,created_at) values(?,?,?)",
                   ("v18.cycle",json.dumps(result),now()))
        result["status"]=self.status()
        return result

    def status(self):
        cs=self._rows("select * from connectors order by name")
        ar=self._rows("select * from action_readiness")
        return {
          "status":"companyos_connector_configuration_credential_readiness_v18_ready",
          "connector_readiness":"ONLINE",
          "action_database":str(self.action_db) if self.action_db else None,
          "actions_total":len(self.actions()),
          "connectors_total":len(cs),
          "connectors_enabled":sum(int(x["enabled"]) for x in cs),
          "credentials_ready":sum(x["credential_state"]=="READY" for x in cs),
          "connectors_healthy":sum(x["health_state"]=="HEALTHY" for x in cs),
          "connectors_configured_untested":sum(x["health_state"]=="CONFIGURED_UNTESTED" for x in cs),
          "actions_eligible_for_nonfinancial_execution":sum(int(x["eligible"]) for x in ar),
          "financial_automation": (
                "ENABLED"
                if all(
                    __import__("json").loads(open(self.cfg).read())
                    .get("policy", {})
                    .get(k, False)
                    for k in (
                        "allow_wallet_signing",
                        "allow_fund_transfer",
                        "allow_spending",
                    )
                )
                else "BLOCKED_BY_POLICY"
            ),
          "config_path":str(self.cfg),
          "dashboard_url":"http://127.0.0.1:9000",
          "updated_at":now()
        }
