
import tempfile
import unittest
from pathlib import Path
from companyos.self_improvement_learning_v23.engine import SelfImprovementLearningV23, write_json

class V23Tests(unittest.TestCase):
    def test_learning_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()
            write_json(live / "enterprise_automation_v15_live.json", {
                "kpis": {"paid_orders": 0, "revenue_usd": 0, "products": 3}
            })
            write_json(live / "validation_launch_director_v20_live.json", {
                "results": [{
                    "venture_id": "v1",
                    "name": "Test Venture",
                    "state": "NEEDS_MORE_VALIDATION",
                    "recommended_price_usd": 49,
                    "blockers": ["weak_source_opportunity_score"]
                }],
                "ready_for_launch_review": 0
            })
            write_json(live / "autonomous_research_network_v22_live.json", {
                "network_enabled": False,
                "evidence_items": 0
            })
            write_json(live / "autonomous_operations_v17_live.json", {
                "operations_health_score": 100,
                "recovery_candidates": []
            })

            engine = SelfImprovementLearningV23(home)
            state = engine.run_cycle()
            self.assertEqual(state["status"], "self_improvement_learning_ready")
            self.assertGreater(state["lessons_generated"], 0)
            self.assertTrue(state["improvement_proposals"])
            self.assertFalse(state["automatic_code_changes_enabled"])
            self.assertTrue((home / "learning_records_v23/organizational_knowledge.json").exists())

if __name__ == "__main__":
    unittest.main()
