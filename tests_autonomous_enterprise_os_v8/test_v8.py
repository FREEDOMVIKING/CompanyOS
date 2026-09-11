import tempfile,unittest
from pathlib import Path
from companyos.autonomous_enterprise_os_v8.core import EnterpriseOSV8

class T(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            c=EnterpriseOSV8(Path(td))
            c.x("INSERT INTO companies VALUES(?,?,?,?,?,?,?)",("c1","Test Co","INCUBATING",84,95,"{}", "x"))
            c.x("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)",("a1","c1","Agent","research",55,0,1,"{}","x"))
            s=c.cycle()["status"]
            self.assertEqual(s["status"],"companyos_autonomous_enterprise_os_v8_ready")
            self.assertGreaterEqual(s["strategic_goals_total"],4)
            self.assertGreaterEqual(s["forecasts_total"],4)
            self.assertGreaterEqual(s["improvement_proposals_total"],1)
            self.assertGreaterEqual(s["sandbox_validated_total"],1)
            self.assertFalse(s["self_improvement"]["automatic_live_code_replacement"])
            self.assertFalse(s["external_actions"]["spending"])
            self.assertFalse(s["external_actions"]["wallet_signing"])
if __name__=="__main__":unittest.main()
