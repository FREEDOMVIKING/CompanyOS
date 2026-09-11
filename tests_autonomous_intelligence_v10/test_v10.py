import tempfile, unittest, json
from pathlib import Path
from companyos.autonomous_intelligence_v10.core import AutonomousIntelligenceV10

class V10Tests(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); c=AutonomousIntelligenceV10(h)
            c.exec("INSERT INTO companies VALUES(?,?,?,?,?,?,?)",("c1","Digital Template Business","INCUBATING",83.75,94,"{}", "x"))
            c.exec("INSERT INTO companies VALUES(?,?,?,?,?,?,?)",("c2","SOP Library","INCUBATING",78,96,"{}", "x"))
            c.exec("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)",("a1","c1","Research Agent","research",100,10,0,"{}","x"))
            c.exec("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)",("a2","c2","Weak Agent","ops",20,1,4,"{}","x"))
            s=c.cycle()["status"]
            self.assertEqual(s["status"],"companyos_autonomous_intelligence_v10_ready")
            self.assertEqual(s["companies_total"],2)
            self.assertGreaterEqual(s["executive_objectives_total"],4)
            self.assertGreaterEqual(s["executive_memories_total"],1)
            self.assertGreaterEqual(s["executive_decisions_total"],1)
            self.assertGreaterEqual(s["workforce_proposals_total"],1)
            self.assertGreaterEqual(s["improvement_proposals_total"],1)
            self.assertGreaterEqual(s["sandbox_validated_total"],1)
            self.assertGreaterEqual(s["plugins_total"],6)
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_config_reflection(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); (h/"config").mkdir()
            (h/"config/external_actions.json").write_text(json.dumps({"publication":True,"wallet_signing":False}))
            s=AutonomousIntelligenceV10(h).status()
            self.assertTrue(s["external_actions_requested"]["publication"])
            self.assertFalse(s["external_actions_requested"]["wallet_signing"])
            self.assertFalse(s["runtime"]["android_process_survival_guaranteed"])

if __name__=="__main__":
    unittest.main()
