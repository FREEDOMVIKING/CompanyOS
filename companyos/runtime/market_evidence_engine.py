from __future__ import annotations
import hashlib,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path

KINDS={"page_view","lead","conversion","revenue"}
def now(): return datetime.now(timezone.utc).isoformat()
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fd,t=tempfile.mkstemp(dir=str(p.parent),prefix=p.name+".")
    with os.fdopen(fd,"w") as f:
        json.dump(d,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
    os.replace(t,p)

class MarketEvidenceEngine:
    def __init__(self,root):
        self.root=Path(root);self.rt=self.root/".companyos_runtime"
        self.events=self.rt/"market_evidence_events.jsonl"
    def _id(self,e):
        raw="|".join(str(e.get(k,"")) for k in ("venture_id","kind","external_id","timestamp","amount"))
        return hashlib.sha256(raw.encode()).hexdigest()[:24]
    def ingest(self,e):
        e=dict(e); kind=e.get("kind")
        if kind not in KINDS: return {"accepted":False,"reason":"unsupported_kind"}
        if not e.get("venture_id"): return {"accepted":False,"reason":"venture_id_required"}
        if kind=="revenue":
            a=e.get("amount")
            if not isinstance(a,(int,float)) or a < 0:return {"accepted":False,"reason":"valid_revenue_amount_required"}
            if not e.get("external_id"):return {"accepted":False,"reason":"revenue_external_id_required"}
        e.setdefault("timestamp",now());e["event_id"]=self._id(e)
        existing=set()
        if self.events.exists():
            for line in self.events.read_text().splitlines():
                try:existing.add(json.loads(line)["event_id"])
                except:pass
        if e["event_id"] in existing:return {"accepted":False,"reason":"duplicate","event_id":e["event_id"]}
        self.events.parent.mkdir(parents=True,exist_ok=True)
        with self.events.open("a") as f:f.write(json.dumps(e,sort_keys=True)+"\n")
        return {"accepted":True,"event_id":e["event_id"]}
    def summarize(self,venture_id):
        xs=[]
        if self.events.exists():
            for line in self.events.read_text().splitlines():
                try:
                    e=json.loads(line)
                    if e.get("venture_id")==venture_id:xs.append(e)
                except:pass
        views=sum(x["kind"]=="page_view" for x in xs);leads=sum(x["kind"]=="lead" for x in xs)
        conv=sum(x["kind"]=="conversion" for x in xs);rev=sum(float(x.get("amount",0)) for x in xs if x["kind"]=="revenue")
        s={"venture_id":venture_id,"timestamp":now(),"events":len(xs),"traffic":views,"leads":leads,
           "conversions":conv,"revenue":round(rev,2),"observed":bool(xs)}
        write_json(self.rt/"market_evidence_summary.json",s);return s
    def score(self,s):
        if not s["observed"]:return {"score":0,"decision":"hold","reason":"no_market_events"}
        score=min(100, min(s["traffic"],100)*.1 + min(s["leads"],20)*2 + min(s["conversions"],10)*5 + min(s["revenue"],500)*.08)
        if s["revenue"]>0 and s["conversions"]>0: decision="scale"
        elif s["leads"]>0 or s["conversions"]>0: decision="improve"
        elif s["traffic"]>=25: decision="improve"
        else: decision="hold"
        return {"score":round(score,2),"decision":decision,"reason":"observed_market_evidence"}
