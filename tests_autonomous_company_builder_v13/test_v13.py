import tempfile, unittest, json
from pathlib import Path
from companyos.autonomous_company_builder_v13.core import AutonomousCompanyBuilderV13
from companyos.autonomous_company_builder_v13.util import now

class V13Tests(unittest.TestCase):
    def test_company_build_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            h=Path(td); c=AutonomousCompanyBuilderV13(h)
            c.db.exec("INSERT INTO companies VALUES(?,?,?,?,?,?,?)",("legacy","Legacy Co","ACTIVE",80,95,"{}",now()))
            c.db.exec("INSERT INTO agents VALUES(?,?,?,?,?,?,?,?,?)",("a1","legacy","Agent","ops",90,1,0,"{}",now()))
            c.db.exec("INSERT INTO venture_handoffs VALUES(?,?,?,?,?,?)",
                      ("h1","p1","READY_FOR_COMPANY_CREATION_REVIEW","Test Venture","{}",now()))
            s=c.cycle()["status"]
            self.assertEqual(s["status"],"companyos_autonomous_company_builder_v13_ready")
            self.assertEqual(s["venture_handoffs_total"],1)
            self.assertEqual(s["launch_queue_total"],1)
            self.assertEqual(s["local_company_builds_total"],1)
            self.assertEqual(s["products_total"],1)
            self.assertEqual(s["marketing_campaigns_total"],1)
            self.assertEqual(s["sales_plans_total"],1)
            self.assertEqual(s["lifecycle_records_total"],1)
            self.assertEqual(s["reinvestment_recommendations_total"],1)
            self.assertFalse(s["automatic_external_publish"])
            self.assertFalse(s["automatic_spending"])

            build=c.db.rows("SELECT * FROM company_builds")[0]
            self.assertTrue(Path(build["website_path"]).exists())

    def test_no_handoff_no_build(self):
        with tempfile.TemporaryDirectory() as td:
            c=AutonomousCompanyBuilderV13(Path(td))
            s=c.cycle()["status"]
            self.assertEqual(s["local_company_builds_total"],0)

if __name__=="__main__":
    unittest.main()
