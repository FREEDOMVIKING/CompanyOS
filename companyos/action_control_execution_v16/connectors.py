import json, shutil, urllib.request
from pathlib import Path
from .util import read_json, write_json, now

DEFAULTS={
 "static_host":{"enabled":True,"mode":"local_publish","publish_root":"~/companyos/published_sites_v16"},
 "analytics":{"enabled":True,"mode":"local_event_log","event_log":"~/companyos/.companyos_enterprise_v16/analytics_events.jsonl"},
 "webhook":{"enabled":False,"mode":"http_post","url":"","timeout_seconds":10},
 "dns_provider":{"enabled":False,"mode":"disabled"},
 "storefront":{"enabled":False,"mode":"disabled"},
 "email_outreach":{"enabled":False,"mode":"disabled"},
 "domain_registrar":{"enabled":False,"mode":"disabled"}
}

class ConnectorManager:
    def __init__(self,home,db):
        self.home=Path(home); self.db=db; self.path=self.home/"config"/"connectors_v16.json"
        if not self.path.exists(): write_json(self.path,DEFAULTS)
    def config(self): return read_json(self.path,DEFAULTS)
    def sync(self):
        n=0
        for name,d in self.config().items():
            cat={"static_host":"hosting","analytics":"analytics","webhook":"integration","dns_provider":"dns","storefront":"commerce","email_outreach":"marketing","domain_registrar":"domain"}.get(name,"integration")
            status="CONFIGURED" if d.get("enabled") else "DISABLED"
            self.db.exec("INSERT OR REPLACE INTO connectors VALUES(?,?,?,?,?,?,?,?,?,?)",
                         (f"connector:{name}",name,cat,status,d.get("mode","disabled"),str(self.path),None,now(),json.dumps(d),now()))
            n+=1
        return n
    def health(self):
        out={}
        for name,d in self.config().items():
            if not d.get("enabled"):
                status,err="DISABLED",None
            elif name=="static_host":
                try:
                    Path(d.get("publish_root")).expanduser().mkdir(parents=True,exist_ok=True)
                    status,err="HEALTHY",None
                except Exception as e: status,err="ERROR",str(e)
            elif name=="analytics":
                try:
                    p=Path(d.get("event_log")).expanduser(); p.parent.mkdir(parents=True,exist_ok=True)
                    status,err="HEALTHY",None
                except Exception as e: status,err="ERROR",str(e)
            elif name=="webhook":
                status,err=("CONFIGURED",None) if d.get("url") else ("ERROR","missing webhook url")
            else:
                status,err="CONFIGURED",None
            self.db.exec("UPDATE connectors SET status=?,last_error=?,last_checked_at=?,updated_at=? WHERE name=?",
                         (status,err,now(),now(),name))
            out[name]={"status":status,"error":err}
        return out
    def execute(self,a):
        cfg=self.config(); name=a["connector_name"]; d=cfg.get(name,{})
        if not d.get("enabled"): return {"ok":False,"status":"CONNECTOR_DISABLED","error":name}
        if a["action_type"]=="PUBLISH_STATIC_SITE" and name=="static_host":
            b=self.db.rows("SELECT * FROM company_builds WHERE company_id=?",(a["company_id"],))
            if not b: return {"ok":False,"status":"NO_BUILD","error":"missing build"}
            src=Path(b[0]["website_path"])
            if not src.exists(): return {"ok":False,"status":"MISSING_SITE","error":str(src)}
            dest=Path(d["publish_root"]).expanduser()/a["company_id"]; dest.mkdir(parents=True,exist_ok=True)
            target=dest/"index.html"; shutil.copy2(src,target)
            return {"ok":True,"status":"EXECUTED","external_ref":str(target)}
        if a["action_type"]=="WRITE_ANALYTICS_EVENT" and name=="analytics":
            p=Path(d["event_log"]).expanduser(); p.parent.mkdir(parents=True,exist_ok=True)
            with p.open("a",encoding="utf-8") as f:
                f.write(json.dumps({"company_id":a["company_id"],"action_id":a["action_id"],"time":now()})+"\n")
            return {"ok":True,"status":"EXECUTED","external_ref":str(p)}
        if a["action_type"]=="POST_WEBHOOK" and name=="webhook":
            url=d.get("url","")
            if not url: return {"ok":False,"status":"CONNECTOR_ERROR","error":"missing url"}
            body=json.dumps({"company_id":a["company_id"],"action_type":a["action_type"],"description":a["description"]}).encode()
            req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="POST")
            try:
                with urllib.request.urlopen(req,timeout=int(d.get("timeout_seconds",10))) as r:
                    return {"ok":200<=r.status<300,"status":"EXECUTED" if 200<=r.status<300 else "HTTP_ERROR","external_ref":url}
            except Exception as e:
                return {"ok":False,"status":"HTTP_ERROR","error":str(e)}
        return {"ok":False,"status":"CONNECTOR_NOT_LIVE","error":"adapter not enabled for live writes"}
