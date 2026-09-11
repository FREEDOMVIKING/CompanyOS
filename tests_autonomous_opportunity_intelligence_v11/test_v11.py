import tempfile, unittest, json
from pathlib import Path
from companyos.autonomous_opportunity_intelligence_v11.core import OpportunityIntelligenceV11
from companyos.autonomous_opportunity_intelligence_v11.util import sid, now

class V11Tests(unittest.TestCase):
    def test_candidate_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); c=OpportunityIntelligenceV11(h)
            c.db.exec("INSERT INTO companies VALUES(?,?,?,?,?,?,?)",("c1","Test Co","ACTIVE",80,95,"{}",now()))
            c.db.exec("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)",("a1","c1","Agent","research",90,1,0,"{}",now()))
            src="s1"
            for i,title in enumerate([
                "Small business automation demand grows",
                "Automation tools for small business operations",
                "Small business workflow automation market"
            ]):
                c.db.exec("""INSERT INTO research_items
                (item_id,source_id,title,url,published_at,summary,category,payload_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (sid("i",i),src,title,f"https://example.com/{i}",now(),"automation demand","business","{}",now()))
            n=c.builder.build()
            self.assertGreaterEqual(n,1)
            self.assertGreaterEqual(len(c.db.rows("SELECT * FROM opportunity_candidates")),1)
            c.builder.queue_validation()
            self.assertGreaterEqual(len(c.db.rows("SELECT * FROM validation_queue")),1)

    def test_default_source_is_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            c=OpportunityIntelligenceV11(Path(td))
            c.sources.sync()
            s=c.status()
            self.assertGreaterEqual(s["research_sources_total"],1)
            self.assertEqual(s["research_sources_enabled"],0)
            self.assertFalse(s["automatic_external_launch"])

if __name__=="__main__":
    unittest.main()
