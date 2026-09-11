import tempfile, unittest
from pathlib import Path
from companyos.unified_core_v5.core import UnifiedCoreV5

class V5Tests(unittest.TestCase):
    def test_foundation_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            (home/".companyos_runtime").mkdir()
            c=UnifiedCoreV5(home)
            c.db.upsert_venture("v1","Digital Template Business","VALIDATE_AND_GROW",83.75,"test",{})
            s=c.run_cycle()
            self.assertEqual(s["status"],"companyos_unified_core_v5_ready")
            self.assertEqual(s["foundation"],"FINAL_ARCHITECTURAL_FOUNDATION")
            self.assertGreaterEqual(s["companies_total"],1)
            self.assertGreaterEqual(s["plugins_total"],10)
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_external_gates_off(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td); (home/".companyos_runtime").mkdir()
            s=UnifiedCoreV5(home).status()
            self.assertFalse(s["external_actions"]["publication"])
            self.assertFalse(s["external_actions"]["spending"])
            self.assertFalse(s["external_actions"]["wallet_signing"])

if __name__=="__main__":
    unittest.main()
