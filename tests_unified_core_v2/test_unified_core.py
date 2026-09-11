import tempfile, unittest
from pathlib import Path
from companyos.unified_core_v2.core import UnifiedCore
from companyos.unified_core_v2.util import atomic_write_json

class UnifiedCoreTests(unittest.TestCase):
    def test_migration_and_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            live = home / ".companyos_runtime"
            live.mkdir()
            atomic_write_json(live/"portfolio_orchestrator_v34_live.json",{
                "status":"portfolio_orchestrator_ready",
                "ventures":[
                    {"venture_id":"v1","name":"Digital Template Business","portfolio_score":83.75,"recommended_action":"VALIDATE_AND_GROW"}
                ]
            })
            atomic_write_json(live/"autonomous_customer_success_v33_live.json",{
                "status":"autonomous_customer_success_ready",
                "customers_total":0
            })
            core = UnifiedCore(home)
            s = core.run_cycle()
            self.assertEqual(s["status"],"companyos_unified_core_ready")
            self.assertGreaterEqual(s["modules_total"],2)
            self.assertEqual(s["ventures_total"],1)
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_external_actions_off(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            (home/".companyos_runtime").mkdir()
            core = UnifiedCore(home)
            s = core.status()
            self.assertFalse(s["external_actions"]["publication"])
            self.assertFalse(s["external_actions"]["wallet_signing"])
            self.assertFalse(s["external_actions"]["spending"])

if __name__=="__main__":
    unittest.main()
