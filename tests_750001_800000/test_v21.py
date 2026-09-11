
import tempfile
import unittest
from pathlib import Path
from companyos.opportunity_intelligence_v21.engine import OpportunityIntelligenceV21, write_json, read_json

class V21Tests(unittest.TestCase):
    def test_scoring_and_manifest_update(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            venture = home / "generated_ventures_v19/test-venture"
            venture.mkdir(parents=True)
            write_json(venture / "venture_manifest.json", {
                "venture_id": "test-venture",
                "name": "Test Venture",
                "state": "NEEDS_MORE_VALIDATION",
                "source_opportunity": {"summary": "Validated internal opportunity", "score": 40}
            })
            write_json(venture / "branding.json", {
                "venture_name": "Test Venture", "tagline": "Useful tools"
            })
            write_json(venture / "offer.json", {
                "primary_offer": "Starter Offer", "price_test_usd": [29,49,79]
            })
            write_json(venture / "economics.json", {
                "estimated_gross_margin_percent": 90,
                "startup_cost_assumption_usd": 0
            })
            write_json(venture / "launch_checklist.json", {"items":[{"step":"review"}]})
            (venture / "landing_page.html").write_text("<html></html>", encoding="utf-8")

            engine = OpportunityIntelligenceV21(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "opportunity_intelligence_ready")
            self.assertEqual(state["opportunities_scored"], 1)
            updated = read_json(venture / "venture_manifest.json", {})
            self.assertGreaterEqual(updated["source_opportunity"]["score"], 60)
            self.assertFalse(state["external_research_provider_connected"])

if __name__ == "__main__":
    unittest.main()
