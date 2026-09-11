
import tempfile
import unittest
from pathlib import Path
from companyos.internet_opportunity_hunter_v27.engine import InternetOpportunityHunterV27, write_json

class V27Tests(unittest.TestCase):
    def test_local_discovery_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            engine = InternetOpportunityHunterV27(home)
            write_json(home / ".companyos_runtime/manual_opportunity_signals_v27.json", {
                "items": [{
                    "title": "Editable estimate templates for field service contractors",
                    "summary": "Small contractors seek faster pricing tools and customer-ready estimate templates.",
                    "estimated_price_usd": 49,
                    "competitor": "ExampleCo",
                    "lead_source": "contractor directories"
                }]
            })
            state = engine.run_cycle()
            self.assertEqual(state["status"], "internet_opportunity_hunter_ready")
            self.assertEqual(state["signals_collected"], 1)
            self.assertEqual(state["opportunities_discovered"], 1)
            self.assertFalse(state["network_enabled"])
            self.assertTrue((home / ".companyos_runtime/approved_opportunities.json").exists())

if __name__ == "__main__":
    unittest.main()
