import tempfile, unittest
from pathlib import Path
from companyos.unified_core_v4.core import UnifiedCoreV4

class V4Tests(unittest.TestCase):
    def test_ceo_planning(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            (home/".companyos_runtime").mkdir()
            c=UnifiedCoreV4(home)
            c.db.upsert_venture("v1","Digital Template Business","VALIDATE_AND_GROW",83.75,"test",{})
            s=c.run_cycle()
            self.assertEqual(s["status"],"companyos_unified_core_v4_ready")
            self.assertGreaterEqual(s["goals_total"],1)
            self.assertIsNotNone(s["latest_executive_decision"])
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_external_gates(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td); (home/".companyos_runtime").mkdir()
            s=UnifiedCoreV4(home).status()
            self.assertFalse(s["external_actions"]["publication"])
            self.assertFalse(s["external_actions"]["spending"])
            self.assertFalse(s["external_actions"]["wallet_signing"])

if __name__=="__main__": unittest.main()
