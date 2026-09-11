import tempfile, unittest, json
from pathlib import Path
from companyos.autonomous_enterprise_network_v7.core import EnterpriseNetworkV7

class V7Tests(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            c=EnterpriseNetworkV7(Path(td))
            c.add_company("c1","Digital Template Business",83.75)
            c.add_company("c2","Micro Business SOP Library",77.8)
            c.ensure_teams()
            s=c.run_cycle()
            self.assertEqual(s["companies_total"],2)
            self.assertGreaterEqual(s["agents_total"],18)
            self.assertGreaterEqual(s["collaborations_total"],1)
            self.assertGreaterEqual(s["tasks"]["completed"],1)

    def test_opportunity(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            c=EnterpriseNetworkV7(home)
            p=home/".companyos_enterprise_v7/opportunities_inbox.json"
            p.write_text(json.dumps({"opportunities":[{
                "name":"Example SaaS","category":"software","demand_score":90,"margin_score":90,
                "execution_score":85,"strategic_fit":90
            }]}))
            s=c.run_cycle()
            self.assertGreaterEqual(s["companies_total"],1)
            self.assertFalse(s["external_actions"]["company_formation"])
            self.assertFalse(s["external_actions"]["spending"])

if __name__=="__main__":
    unittest.main()
