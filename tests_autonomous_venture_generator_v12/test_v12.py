import tempfile, unittest
from pathlib import Path
from companyos.autonomous_venture_generator_v12.core import AutonomousVentureGeneratorV12
from companyos.autonomous_venture_generator_v12.util import now

class V12Tests(unittest.TestCase):
    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); c=AutonomousVentureGeneratorV12(h)
            c.db.exec("INSERT INTO companies VALUES(?,?,?,?,?,?,?)",("c1","Test Co","ACTIVE",80,95,"{}",now()))
            c.db.exec("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)",("a1","c1","Agent","research",90,1,0,"{}",now()))
            c.db.exec("INSERT INTO opportunities VALUES(?,?,?,?,?,?,?,?)",
                      ("o1","Automation Opportunity","business","VALIDATE_MORE",82.5,5,"{}",now()))
            s=c.cycle()["status"]
            self.assertEqual(s["status"],"companyos_autonomous_venture_generator_v12_ready")
            self.assertEqual(s["opportunities_total"],1)
            self.assertGreaterEqual(s["venture_proposals_total"],1)
            self.assertGreaterEqual(s["business_plans_total"],1)
            self.assertGreaterEqual(s["milestones_total"],6)
            self.assertGreaterEqual(s["launch_packages_total"],1)
            self.assertGreaterEqual(s["executive_reviews_total"],1)
            self.assertGreaterEqual(s["company_handoffs_total"],1)
            self.assertFalse(s["automatic_external_launch"])
            self.assertFalse(s["automatic_company_creation"])

    def test_hold_low_score(self):
        with tempfile.TemporaryDirectory() as td:
            c=AutonomousVentureGeneratorV12(Path(td))
            c.db.exec("INSERT INTO opportunities VALUES(?,?,?,?,?,?,?,?)",
                      ("o2","Weak Opportunity","general","VALIDATE_MORE",66,2,"{}",now()))
            c.generator.build()
            row=c.db.rows("SELECT * FROM venture_proposals")[0]
            self.assertIn(row["status"],("READY_FOR_PLAN","HOLD_AND_VALIDATE"))

if __name__=="__main__":
    unittest.main()
