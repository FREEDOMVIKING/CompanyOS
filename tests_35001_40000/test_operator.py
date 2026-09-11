import tempfile,unittest
from pathlib import Path
from companyos.executive_memory.engine import ExecutiveMemory
from companyos.strategic_planner.engine import StrategicPlanner
from companyos.project_manager.engine import ProjectManager
from companyos.workforce_manager.engine import WorkforceManager
from companyos.vendor_procurement.engine import VendorProcurement
from companyos.customer_support.engine import CustomerSupport
from companyos.risk_compliance.engine import RiskCompliance
from companyos.financial_forecasting.engine import FinancialForecasting
from companyos.resource_allocator.engine import ResourceAllocator
from companyos.multi_company_orchestrator.engine import MultiCompanyOrchestrator

class Tests(unittest.TestCase):
    def test_memory(self):
        with tempfile.TemporaryDirectory() as t:
            r=ExecutiveMemory(Path(t)).run()
            self.assertEqual(r["phase"],"35001-40000")

    def test_strategy(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("priorities",StrategicPlanner(Path(t)).run())

    def test_project(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(ProjectManager(Path(t)).run()["status"],"waiting_for_venture")

    def test_workforce(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(WorkforceManager(Path(t)).run()["agent_count"],0)

    def test_vendor_support_risk(self):
        with tempfile.TemporaryDirectory() as t:
            h=Path(t)
            self.assertEqual(VendorProcurement(h).run()["commitments"],"approval_required")
            self.assertEqual(CustomerSupport(h).run()["status"],"active")
            self.assertIn("controls",RiskCompliance(h).run())

    def test_forecast_allocator(self):
        with tempfile.TemporaryDirectory() as t:
            h=Path(t)
            self.assertIn("forecast",FinancialForecasting(h).run())
            self.assertEqual(ResourceAllocator(h).run()["allocations"],[])

    def test_multi_company(self):
        with tempfile.TemporaryDirectory() as t:
            r=MultiCompanyOrchestrator(Path(t)).run()
            self.assertEqual(r["phase"],"35001-40000")
            self.assertEqual(r["company_count"],0)

if __name__=="__main__":
    unittest.main()
