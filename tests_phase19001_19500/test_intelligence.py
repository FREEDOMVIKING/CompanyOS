import tempfile, unittest
from pathlib import Path
from companyos.intelligence.portfolio import portfolio_health, rank_opportunities, allocate_shared_resources
from companyos.intelligence.council import executive_council
from companyos.intelligence.strategy import strategic_plan
from companyos.intelligence.learning import derive_playbooks
from companyos.intelligence.engine import ExecutiveIntelligenceEngine

class Tests(unittest.TestCase):
    def test_portfolio_health(self):
        r=portfolio_health([{"health_score":0.8},{"health_score":0.2}])
        self.assertEqual(r["healthy"],1)
        self.assertEqual(r["critical"],1)

    def test_opportunity_rank(self):
        r=rank_opportunities([
            {"venture_id":"a","priority_score":2,"health_score":0.8,"confidence":0.9,"risk":0.2},
            {"venture_id":"b","priority_score":0.1,"health_score":0.2,"confidence":0.2,"risk":0.8},
        ])
        self.assertEqual(r[0]["venture_id"],"a")

    def test_resource_sum(self):
        r=allocate_shared_resources([{"venture_id":"a"},{"venture_id":"b"}])
        self.assertAlmostEqual(sum(x["capacity_share"] for x in r),1.0,places=3)

    def test_council(self):
        r=executive_council([],[],{"deployable":0})
        self.assertEqual(len(r),5)

    def test_strategy(self):
        r=strategic_plan([{"venture_id":"a","name":"A","recommended_posture":"accelerate"}],[],{"score":0.8})
        self.assertEqual(r["portfolio_posture"],"growth")

    def test_playbook(self):
        r=derive_playbooks([{"lesson":"Preserve reserve."}],[])
        self.assertEqual(len(r),1)

    def test_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            (home/"companyos_runtime"/"opscenter").mkdir(parents=True)
            (home/"companyos_runtime"/"orchestrator").mkdir(parents=True)
            r=ExecutiveIntelligenceEngine(home).run_cycle()
            self.assertEqual(r["phase"],"19001-19500")
            self.assertTrue((home/"companyos_runtime"/"intelligence"/"latest_intelligence.json").exists())

if __name__=="__main__":
    unittest.main()
