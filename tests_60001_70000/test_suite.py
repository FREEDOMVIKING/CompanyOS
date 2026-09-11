import tempfile,unittest
from pathlib import Path
from companyos.product_factory_v2.engine import ProductFactoryV2
from companyos.task_delegation_v2.engine import TaskDelegationV2
from companyos.crm_automation_v2.engine import CRMAutomationV2
from companyos.proposal_contracts_v2.engine import ProposalContractsV2
from companyos.vendor_bidding_v2.engine import VendorBiddingV2
from companyos.acquisition_scanner_v2.engine import AcquisitionScannerV2
from companyos.revenue_optimizer_v4.engine import RevenueOptimizerV4
from companyos.qa_recovery_v2.engine import QARecoveryV2
from companyos.executive_analytics_v3.engine import ExecutiveAnalyticsV3
from companyos.unified_runtime_controller.engine import UnifiedRuntimeController
class T(unittest.TestCase):
 def test_all(self):
  with tempfile.TemporaryDirectory() as t:
   h=Path(t);self.assertTrue(Path(ProductFactoryV2(h).run()["product_dir"]).exists());self.assertIn("assignments",TaskDelegationV2(h).run());self.assertIn("pipeline",CRMAutomationV2(h).run());self.assertTrue(Path(ProposalContractsV2(h).run()["proposal_file"]).exists());self.assertTrue(VendorBiddingV2(h).run()["bids"]);self.assertIn("targets",AcquisitionScannerV2(h).run());self.assertIn("actions",RevenueOptimizerV4(h).run());self.assertIn("log_count",QARecoveryV2(h).run());self.assertEqual(ExecutiveAnalyticsV3(h).run()["phase"],"60001-70000");self.assertIn("companyos_process_count",UnifiedRuntimeController(h).run())
if __name__=="__main__":unittest.main()
