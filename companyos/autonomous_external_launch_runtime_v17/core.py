from __future__ import annotations
import json, os, sqlite3, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path.home()/"companyos"
CFG=ROOT/"config"/"external_launch_v17.json"
STATE=ROOT/"ceo_memory"/"v17_external_launch_state.json"
SAFE={"APPLY_DNS","CREATE_STOREFRONT","PUBLISH_STATIC_SITE","START_OUTREACH"}
FINANCIAL={"PURCHASE_DOMAIN","SPENDING","FUND_TRANSFER","WALLET_SIGNING"}
def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(Path(p).read_text())
    except Exception:return d
def save(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True))
class ExternalLaunchRuntimeV17:
    def __init__(self): self.cfg=load(CFG,{});self.db=self._db()
    def _db(self):
        for p in sorted(ROOT.glob(".*/*.sqlite3"),key=lambda x:x.stat().st_mtime,reverse=True):
            try:
                c=sqlite3.connect(p); names={r[0] for r in c.execute("select name from sqlite_master where type='table'")};c.close()
                if "actions" in names:return p
            except Exception:pass
        raise RuntimeError("No action database found")
    def rows(self):
        c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row;r=[dict(x) for x in c.execute("select * from actions order by rowid")];c.close();return r
    def cols(self):
        c=sqlite3.connect(self.db);x={r[1] for r in c.execute("pragma table_info(actions)")};c.close();return x
    def connector_ready(self,t):
        x=self.cfg.get("connectors",{}).get(t,{});return bool(x.get("enabled") and x.get("command"))
    def approve_safe(self):
        c=sqlite3.connect(self.db);q="update actions set status='APPROVED' where upper(action_type) in (?,?,?,?) and upper(status)='REVIEW_REQUIRED'";cur=c.execute(q,tuple(sorted(SAFE)));c.commit();n=cur.rowcount;c.close();return {"approved":n,"financial_actions_untouched":True}
    def execute(self,a):
        t=str(a.get("action_type","")).upper()
        if t not in SAFE:return {"ok":False,"skipped":True,"reason":"policy_blocked"}
        x=self.cfg.get("connectors",{}).get(t,{})
        if not x.get("enabled") or not x.get("command"):return {"ok":False,"skipped":True,"reason":"connector_not_configured"}
        e=os.environ.copy();e["COMPANYOS_ACTION_JSON"]=json.dumps(a);e["COMPANYOS_ACTION_ID"]=str(a.get("action_id",""))
        try:
            p=subprocess.run(x["command"],shell=True,cwd=ROOT,env=e,text=True,capture_output=True,timeout=int(x.get("timeout_seconds",90)))
            return {"ok":p.returncode==0,"returncode":p.returncode,"stdout":p.stdout[-4000:],"stderr":p.stderr[-4000:]}
        except Exception as z:return {"ok":False,"error":repr(z)}
    def cycle(self):
        st=load(STATE,{"cycles":0,"receipts":[]});st["cycles"]+=1;ex=fa=sk=0;cols=self.cols()
        for a in self.rows():
            if str(a.get("status","")).upper() not in {"APPROVED","READY"}:continue
            r=self.execute(a);st["receipts"].append({"receipt_id":uuid.uuid4().hex,"at":now(),"action_id":a.get("action_id"),"action_type":a.get("action_type"),"result":r})
            if r.get("skipped"):sk+=1;continue
            ns="EXECUTED" if r.get("ok") else "FAILED";ex+=int(r.get("ok",False));fa+=int(not r.get("ok",False))
            if "status" in cols and "action_id" in cols:
                c=sqlite3.connect(self.db);c.execute("update actions set status=? where action_id=?",(ns,a.get("action_id")));c.commit();c.close()
        st["receipts"]=st["receipts"][-500:];st["last_result"]={"executed":ex,"failed":fa,"skipped":sk};st["last_cycle_at"]=now();save(STATE,st);return st["last_result"]
    def status(self):
        counts={}
        for a in self.rows():counts[str(a.get("status","UNKNOWN")).upper()]=counts.get(str(a.get("status","UNKNOWN")).upper(),0)+1
        return {"status":"companyos_autonomous_external_launch_runtime_v17_ready","runtime":"ONLINE","database":str(self.db),"action_status_counts":counts,"connectors":{t:self.connector_ready(t) for t in sorted(SAFE)},"financial_automation":"BLOCKED_BY_V17","state":load(STATE,{})}
