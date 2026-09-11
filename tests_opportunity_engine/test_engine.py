import tempfile,unittest
from pathlib import Path
from companyos.opportunity_engine.engine import (
    OpportunityEngine,evidence_summary,competitor_analysis,
    demand_estimate,trend_estimate,profitability,opportunity_score,DEFAULT_WEIGHTS
)

class Tests(unittest.TestCase):
    def test_evidence(self):
        self.assertEqual(evidence_summary(["a","b"])["evidence_count"],2)

    def test_competitors(self):
        self.assertEqual(competitor_analysis([{"price":100},{"price":200}])["average_price"],150.0)

    def test_forecasting(self):
        demand=demand_estimate({"pain_severity":1},0.5)
        self.assertGreater(demand,0)
        self.assertIn(trend_estimate({})["label"],{"rising","stable","declining"})
        self.assertIn("monthly_profit",profitability({},demand))

    def test_score_bounds(self):
        value=opportunity_score(1,{"score":1},{"margin":1},{"score":0},1,DEFAULT_WEIGHTS)
        self.assertGreaterEqual(value,0)
        self.assertLessEqual(value,1)

    def test_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine=OpportunityEngine(Path(tmp))
            engine.add("Test","Problem","Customer")
            result=engine.run_cycle()
            self.assertEqual(result["phase"],"23001-25000")
            self.assertEqual(result["opportunity_count"],1)
            self.assertTrue((Path(tmp)/"companyos_runtime"/"opportunity_engine"/"pipeline.json").exists())

    def test_default_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=OpportunityEngine(Path(tmp)).run_cycle()
            self.assertEqual(result["opportunity_count"],1)

if __name__=="__main__":
    unittest.main()
