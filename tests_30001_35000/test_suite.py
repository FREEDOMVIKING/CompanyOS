import tempfile,unittest
from pathlib import Path
from companyos.ceo_planner.engine import CEOPlanner
from companyos.launch_engine.engine import LaunchEngine
from companyos.sales_engine.engine import SalesEngine
from companyos.finance_manager.engine import FinanceManager
from companyos.learning_engine.engine import LearningEngine
from companyos.executive_dashboard_v2.engine import DashboardV2
from companyos.growth_suite.core import portfolio_snapshot

class Tests(unittest.TestCase):
    def test_ceo_plan(self):
        with tempfile.TemporaryDirectory() as t:
            r=CEOPlanner(Path(t)).run()
            self.assertEqual(r["phase"],"30001-35000")
            self.assertTrue(r["objectives"])

    def test_launch(self):
        with tempfile.TemporaryDirectory() as t:
            r=LaunchEngine(Path(t)).run()
            self.assertEqual(r["status"],"waiting_for_venture")

    def test_sales(self):
        with tempfile.TemporaryDirectory() as t:
            r=SalesEngine(Path(t)).run()
            self.assertIn("pipeline",r)

    def test_finance(self):
        with tempfile.TemporaryDirectory() as t:
            r=FinanceManager(Path(t)).run()
            self.assertEqual(r["financial_execution"],"proposal_only_until_connector_and_policy_allow")

    def test_learning(self):
        with tempfile.TemporaryDirectory() as t:
            r=LearningEngine(Path(t)).run()
            self.assertTrue(r["lessons"])

    def test_dashboard(self):
        with tempfile.TemporaryDirectory() as t:
            r=DashboardV2(Path(t)).snapshot()
            self.assertEqual(r["phase"],"30001-35000")

    def test_portfolio(self):
        with tempfile.TemporaryDirectory() as t:
            r=portfolio_snapshot(Path(t))
            self.assertEqual(r["portfolio_size"],0)

if __name__=="__main__":
    unittest.main()
