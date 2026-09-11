import tempfile, unittest
from pathlib import Path
from companyos.unified_core_v3.core import UnifiedCoreV3
from companyos.unified_core_v3.util import atomic_write_json

class V3Tests(unittest.TestCase):
    def test_cycle_and_plugins(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            live=home/".companyos_runtime"
            live.mkdir()
            atomic_write_json(live/"portfolio_orchestrator_v34_live.json",{
                "status":"portfolio_orchestrator_ready",
                "ventures":[{"venture_id":"v1","name":"Digital Template Business","portfolio_score":83.75,"recommended_action":"VALIDATE_AND_GROW"}]
            })
            core=UnifiedCoreV3(home)
            core.db.upsert_venture("v1","Digital Template Business","VALIDATE_AND_GROW",83.75,"test",{})
            s=core.run_cycle()
            self.assertEqual(s["status"],"companyos_unified_core_v3_ready")
            self.assertGreaterEqual(s["plugins_total"],8)
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_external_actions_off(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            (home/".companyos_runtime").mkdir()
            s=UnifiedCoreV3(home).status()
            self.assertFalse(s["external_actions"]["publication"])
            self.assertFalse(s["external_actions"]["spending"])
            self.assertFalse(s["external_actions"]["wallet_signing"])

if __name__=="__main__": unittest.main()
