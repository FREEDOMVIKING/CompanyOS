import tempfile, unittest
from pathlib import Path
from companyos.autonomous_enterprise_v6.core import EnterpriseCoreV6

class V6Tests(unittest.TestCase):
    def test_enterprise_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            c=EnterpriseCoreV6(home)
            c.db.upsert_company("c1","Digital Template Business","INCUBATING","v1",83.75,{})
            s=c.run_cycle()
            self.assertEqual(s["status"],"companyos_autonomous_enterprise_v6_ready")
            self.assertEqual(s["companies_total"],1)
            self.assertGreaterEqual(s["agents_total"],9)
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_provider_fallback_and_gates(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            c=EnterpriseCoreV6(home)
            s=c.status()
            self.assertTrue(s["provider"]["local_fallback_enabled"])
            self.assertFalse(s["external_actions"]["publication"])
            self.assertFalse(s["external_actions"]["spending"])
            self.assertFalse(s["external_actions"]["wallet_signing"])

if __name__=="__main__":
    unittest.main()
