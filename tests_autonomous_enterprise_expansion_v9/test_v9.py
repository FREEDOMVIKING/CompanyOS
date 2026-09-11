import tempfile, unittest, json
from pathlib import Path
from companyos.autonomous_enterprise_expansion_v9.core import EnterpriseExpansionV9

class V9Tests(unittest.TestCase):
    def test_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            c=EnterpriseExpansionV9(home)
            c.db.upsert_company("c1","Digital Template Business","INCUBATING",83.75,94,{})
            c.db.upsert_company("c2","SOP Library","INCUBATING",77.8,97,{})
            c.db.upsert_agent("a1","c2","Ops Agent","operations",True,10,0,100,{})
            s=c.cycle()
            self.assertEqual(s["status"],"companyos_autonomous_enterprise_expansion_v9_ready")
            self.assertEqual(s["companies_total"],2)
            self.assertGreaterEqual(s["executive_memories_total"],1)
            self.assertGreaterEqual(s["capital_plans_total"],2)
            self.assertGreaterEqual(s["tasks"]["completed"],1)
            self.assertFalse(s["external_actions"]["spending"])

    def test_opportunity(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            c=EnterpriseExpansionV9(home)
            inbox=home/".companyos_enterprise_v9/opportunities_inbox.json"
            inbox.parent.mkdir(parents=True,exist_ok=True)
            inbox.write_text(json.dumps({"opportunities":[{
                "name":"Example AI Service","category":"software",
                "demand_score":90,"margin_score":90,"execution_score":85,"strategic_fit":90
            }]}),encoding="utf-8")
            s=c.cycle()
            self.assertEqual(s["high_priority_opportunities"],1)
            self.assertFalse(s["external_actions"]["publication"])
            self.assertFalse(s["external_actions"]["wallet_signing"])

if __name__=="__main__":
    unittest.main()
