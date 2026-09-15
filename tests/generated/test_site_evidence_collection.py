from companyos.runtime.site_evidence_collector import Collector
from companyos.runtime.site_instrumentation import instrument
def test_public_collector_rejects_revenue(tmp_path):
 assert Collector(tmp_path).ingest({"venture_id":"v","kind":"revenue","amount":999})["accepted"] is False
def test_collector_records_attributed_visit(tmp_path):
 c=Collector(tmp_path);assert c.ingest({"venture_id":"v","kind":"page_view","event_id":"pv1","timestamp":"T"})["accepted"]
 assert c.engine.summarize("v")["traffic"]==1
def test_instrumentation(tmp_path):
 d=tmp_path/"site";d.mkdir();(d/"index.html").write_text("<body><form></form></body>")
 r=instrument(d,"venture-1","https://collector.example")
 s=(d/"index.html").read_text()
 assert r["instrumented"] and "companyos-evidence-v1" in s and "venture-1" in s
def test_no_sensitive_browser_collection(tmp_path):
 d=tmp_path/"site";d.mkdir();(d/"index.html").write_text("<body></body>")
 instrument(d,"v","https://x")
 s=(d/"index.html").read_text().lower()
 assert "geolocation" not in s and "fingerprint" not in s and "cookie" not in s
