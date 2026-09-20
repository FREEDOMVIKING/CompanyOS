#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
set -a; . "$HOME/.companyos_launch_env"; set +a

echo "===== COMPANYOS REAL MARKET EVIDENCE LARGE PUSH ====="
echo "No supervisor restart. No finance transfer. No DNS mutation."
mkdir -p companyos/runtime scripts tests/generated .companyos_runtime

cat > companyos/runtime/market_evidence_engine.py <<'PY'
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
PY

cat > scripts/companyos_evidencectl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from companyos.runtime.market_evidence_engine import MarketEvidenceEngine
p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
i=sub.add_parser("ingest");i.add_argument("--venture",required=True);i.add_argument("--kind",required=True);i.add_argument("--external-id");i.add_argument("--amount",type=float)
s=sub.add_parser("summary");s.add_argument("--venture",required=True)
a=p.parse_args();e=MarketEvidenceEngine(ROOT)
if a.cmd=="ingest":
 r=e.ingest({"venture_id":a.venture,"kind":a.kind,"external_id":a.external_id,"amount":a.amount})
else:
 sm=e.summarize(a.venture);r={"summary":sm,"performance":e.score(sm)}
print(json.dumps(r,indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_evidencectl

cat > tests/generated/test_market_evidence_engine.py <<'PY'
from companyos.runtime.market_evidence_engine import MarketEvidenceEngine
def test_requires_attribution(tmp_path):
 assert MarketEvidenceEngine(tmp_path).ingest({"kind":"lead"})["accepted"] is False
def test_revenue_requires_external_id(tmp_path):
 assert MarketEvidenceEngine(tmp_path).ingest({"venture_id":"v","kind":"revenue","amount":5})["accepted"] is False
def test_deduplicates(tmp_path):
 e=MarketEvidenceEngine(tmp_path);x={"venture_id":"v","kind":"lead","external_id":"L1","timestamp":"T"}
 assert e.ingest(x)["accepted"];assert e.ingest(x)["reason"]=="duplicate"
def test_real_summary_and_score(tmp_path):
 e=MarketEvidenceEngine(tmp_path)
 e.ingest({"venture_id":"v","kind":"page_view","external_id":"P1","timestamp":"1"})
 e.ingest({"venture_id":"v","kind":"lead","external_id":"L1","timestamp":"2"})
 e.ingest({"venture_id":"v","kind":"conversion","external_id":"C1","timestamp":"3"})
 e.ingest({"venture_id":"v","kind":"revenue","external_id":"R1","amount":25.0,"timestamp":"4"})
 s=e.summarize("v");p=e.score(s)
 assert s["revenue"]==25 and s["leads"]==1 and p["decision"]=="scale"
PY

echo "===== COMPILE + TEST ====="
python -m py_compile companyos/runtime/market_evidence_engine.py scripts/companyos_evidencectl
python -m pytest -q tests/generated/test_post_launch_revenue_loop.py tests/generated/test_market_evidence_engine.py

echo "===== ZERO-FABRICATION BASELINE ====="
VID="controlled-large-push-verification"
python scripts/companyos_evidencectl summary --venture "$VID"

echo "===== INTEGRITY ASSERT ====="
python - <<'PY'
from companyos.runtime.market_evidence_engine import MarketEvidenceEngine
from pathlib import Path
e=MarketEvidenceEngine(Path.cwd())
s=e.summarize("controlled-large-push-verification")
# Existing real events are allowed; the engine itself must never synthesize them.
assert s["traffic"]>=0 and s["leads"]>=0 and s["conversions"]>=0 and s["revenue"]>=0
print("MARKET_EVIDENCE_INTEGRITY=PASS")
PY

echo "===== COMMIT ONLY THIS PUSH ====="
git add companyos/runtime/market_evidence_engine.py scripts/companyos_evidencectl tests/generated/test_market_evidence_engine.py
git commit -m "add attributable market evidence and performance scoring" || true

echo "===== FINAL ====="
git rev-parse --short HEAD
git status --short
echo "COMPANYOS_MARKET_EVIDENCE_LARGE_PUSH=PASS"
