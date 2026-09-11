
import tempfile
import unittest
from pathlib import Path
from companyos.autonomous_research_network_v22.engine import AutonomousResearchNetworkV22, write_json

class V22Tests(unittest.TestCase):
    def test_local_evidence_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            venture = home / "generated_ventures_v19/digital-template-business"
            venture.mkdir(parents=True)
            write_json(venture / "venture_manifest.json", {
                "venture_id": "digital-template-business",
                "name": "Digital Template Business"
            })
            engine = AutonomousResearchNetworkV22(home)
            write_json(home / ".companyos_runtime/manual_research_evidence.json", {
                "items": [{
                    "title": "Template demand continues among small businesses",
                    "summary": "Customers seek editable business templates.",
                    "price_usd": 49,
                    "competitor": "Example Competitor"
                }]
            })
            state = engine.run_cycle()
            self.assertEqual(state["status"], "autonomous_research_network_ready")
            self.assertEqual(state["evidence_items"], 1)
            item = state["venture_evidence"]["digital-template-business"]
            self.assertEqual(item["matched_items"], 1)
            self.assertFalse(state["network_enabled"])

if __name__ == "__main__":
    unittest.main()
