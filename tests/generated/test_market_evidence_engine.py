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
