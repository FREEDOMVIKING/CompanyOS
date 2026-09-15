from __future__ import annotations
import json, os, tempfile, urllib.request
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def read_json(p,d=None):
    try:return json.loads(Path(p).read_text())
    except Exception:return {} if d is None else d
def write_json(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(data,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class PostLaunchRevenueLoop:
    """Evidence-driven post-launch controller.

    Never invents revenue/conversions. Unknown metrics stay unknown.
    Decisions are bounded to improve/scale/hold/kill recommendations.
    Financial, credential, DNS and irreversible external actions remain outside.
    """
    def __init__(self,root):
        self.root=Path(root); self.rt=self.root/".companyos_runtime"

    def latest_launch(self):
        return read_json(self.rt/"venture_launch_latest.json",{})

    def collect_public_evidence(self,launch):
        url=launch.get("public_url")
        e={"timestamp":now(),"public_url":url,"site_reachable":False,"http_status":None,
           "revenue":None,"leads":None,"conversions":None,"traffic":None,
           "evidence_quality":"availability_only"}
        if not url:return e
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CompanyOS-Evidence/1.0"})
            with urllib.request.urlopen(req,timeout=20) as r:
                e["http_status"]=getattr(r,"status",200)
                e["site_reachable"]=200 <= e["http_status"] < 400
        except Exception as x:
            e["error"]=str(x)[:500]
        return e

    def decide(self,launch,evidence):
        if launch.get("status")!="launched":
            return {"decision":"hold","reason":"no_active_launched_venture","confidence":1.0}
        if not evidence.get("site_reachable"):
            return {"decision":"improve","reason":"public_site_unreachable","confidence":0.95,
                    "next_action":"diagnose_and_restore_public_site"}
        revenue=evidence.get("revenue"); conversions=evidence.get("conversions")
        if isinstance(revenue,(int,float)) and revenue > 0:
            return {"decision":"scale","reason":"observed_positive_revenue","confidence":0.9,
                    "next_action":"increase_validated_distribution_within_existing_gates"}
        if isinstance(conversions,(int,float)) and conversions > 0:
            return {"decision":"improve","reason":"observed_conversion_without_revenue_evidence","confidence":0.8,
                    "next_action":"improve_offer_and_revenue_capture"}
        return {"decision":"hold","reason":"insufficient_market_evidence","confidence":0.9,
                "next_action":"acquire_real_traffic_lead_conversion_and_revenue_evidence"}

    def run(self):
        launch=self.latest_launch()
        evidence=self.collect_public_evidence(launch)
        decision=self.decide(launch,evidence)
        record={"timestamp":now(),"venture":launch.get("title"),"opportunity_id":launch.get("opportunity_id"),
                "public_url":launch.get("public_url"),"evidence":evidence,**decision}
        write_json(self.rt/"post_launch_revenue_latest.json",record)
        with (self.rt/"post_launch_revenue_ledger.jsonl").open("a") as f:f.write(json.dumps(record,sort_keys=True)+"\n")
        request={"timestamp":now(),"source":"post_launch_revenue_loop","opportunity_id":record.get("opportunity_id"),
                 "decision":record["decision"],"reason":record["reason"],"next_action":record.get("next_action"),
                 "public_url":record.get("public_url"),"requires_real_evidence":True}
        write_json(self.rt/"post_launch_next_action.json",request)
        with (self.rt/"outcome_evidence_queue.jsonl").open("a") as f:f.write(json.dumps({"kind":"post_launch_evidence",**record},sort_keys=True)+"\n")
        return record
