import json
from datetime import datetime, timezone, timedelta
from .util import sid, now
from .policy import ActionPolicy

class ActionExecutor:
    def __init__(self,db,connectors):
        self.db=db; self.connectors=connectors; self.policy=ActionPolicy()

    def review_all(self):
        reviewed=blocked=0
        for a in self.db.rows("SELECT * FROM actions"):
            p=self.policy.classify(a)
            status="BLOCKED_POLICY" if p["decision"]=="BLOCK_AUTOMATION" else a["status"]
            self.db.exec("UPDATE actions SET policy_decision=?,status=?,updated_at=? WHERE action_id=?",
                         (p["decision"],status,now(),a["action_id"]))
            reviewed+=1; blocked+=int(status=="BLOCKED_POLICY")
        return {"reviewed":reviewed,"blocked":blocked}

    def approve(self,action_id):
        rows=self.db.rows("SELECT * FROM actions WHERE action_id=?",(action_id,))
        if not rows: return {"ok":False,"error":"action_not_found"}
        a=rows[0]; p=self.policy.classify(a)
        if p["decision"]=="BLOCK_AUTOMATION":
            return {"ok":False,"error":"policy_blocked"}
        self.db.exec("UPDATE actions SET status='APPROVED',policy_decision=?,updated_at=? WHERE action_id=?",
                     (p["decision"],now(),action_id))
        self.db.audit("action.approved",a["company_id"],"control_plane","APPROVED",{"action_id":action_id})
        return {"ok":True,"action_id":action_id}

    def approve_safe_batch(self):
        approved=[]
        for a in self.db.rows("SELECT * FROM actions WHERE status='REVIEW_REQUIRED'"):
            if a["action_type"] in ("PUBLISH_STATIC_SITE","WRITE_ANALYTICS_EVENT","POST_WEBHOOK"):
                if self.policy.classify(a)["decision"]!="BLOCK_AUTOMATION":
                    self.db.exec("UPDATE actions SET status='APPROVED',updated_at=? WHERE action_id=?",(now(),a["action_id"]))
                    approved.append(a["action_id"])
        return {"approved":approved}

    def retry(self,action_id):
        rows=self.db.rows("SELECT * FROM actions WHERE action_id=?",(action_id,))
        if not rows: return {"ok":False,"error":"action_not_found"}
        a=rows[0]
        if int(a["attempts"] or 0)>=5: return {"ok":False,"error":"retry_limit_reached"}
        if a["status"] not in ("FAILED","HTTP_ERROR","CONNECTOR_ERROR","CONNECTOR_NOT_LIVE","CONNECTOR_DISABLED","NO_BUILD","MISSING_SITE"):
            return {"ok":False,"error":"action_not_retryable","status":a["status"]}
        self.db.exec("UPDATE actions SET status='APPROVED',next_retry_at=NULL,updated_at=? WHERE action_id=?",(now(),action_id))
        return {"ok":True,"action_id":action_id}

    def execute(self):
        out={"executed":0,"failed":0,"blocked":0}
        for a in self.db.rows("SELECT * FROM actions WHERE status='APPROVED' ORDER BY updated_at LIMIT 100"):
            if self.policy.classify(a)["decision"]=="BLOCK_AUTOMATION":
                self.db.exec("UPDATE actions SET status='BLOCKED_POLICY',updated_at=? WHERE action_id=?",(now(),a["action_id"]))
                out["blocked"]+=1; continue
            r=self.connectors.execute(a)
            attempts=int(a["attempts"] or 0)+1
            status="EXECUTED" if r.get("ok") else r.get("status","FAILED")
            retry_at=None
            if not r.get("ok") and attempts<5:
                retry_at=(datetime.now(timezone.utc)+timedelta(seconds=min(3600,30*(2**(attempts-1))))).isoformat()
            self.db.exec("UPDATE actions SET status=?,attempts=?,next_retry_at=?,last_error=?,updated_at=? WHERE action_id=?",
                         (status,attempts,retry_at,r.get("error"),now(),a["action_id"]))
            self.db.exec("INSERT INTO receipts VALUES(?,?,?,?,?,?,?,?)",
                         (sid("receipt",a["action_id"],attempts,now()),a["action_id"],a["company_id"],a["connector_name"],
                          status,r.get("external_ref"),json.dumps(r),now()))
            self._score(a["company_id"],status)
            self.db.audit("action.execution",a["company_id"],"v16_executor",status,{"action_id":a["action_id"],"result":r})
            out["executed" if r.get("ok") else "failed"]+=1
        return out

    def _score(self,company_id,status):
        rows=self.db.rows("SELECT * FROM execution_scores WHERE company_id=?",(company_id,))
        if rows:
            x=rows[0]; s=int(x["successes"]); f=int(x["failures"]); b=int(x["blocked"])
        else: s=f=b=0
        if status=="EXECUTED": s+=1
        elif status.startswith("BLOCKED"): b+=1
        else: f+=1
        total=max(1,s+f+b); score=round((s*100+b*50)/total,2)
        self.db.exec("INSERT OR REPLACE INTO execution_scores VALUES(?,?,?,?,?,?,?)",
                     (company_id,s,f,b,score,status,now()))
