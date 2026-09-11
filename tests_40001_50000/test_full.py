import tempfile,unittest
from pathlib import Path
from companyos.code_generation.engine import CodeGenerationEngine
from companyos.website_deployer.engine import WebsiteDeployer
from companyos.domain_orchestrator.engine import DomainOrchestrator
from companyos.customer_acquisition_v2.engine import CustomerAcquisitionV2
from companyos.competitor_intelligence.engine import CompetitorIntelligence
from companyos.negotiation_engine.engine import NegotiationEngine
from companyos.ceo_council_v2.engine import CEOCouncilV2
from companyos.memory_graph.engine import MemoryGraph
from companyos.self_evolution.engine import SelfEvolution
from companyos.profitability_optimizer.engine import ProfitabilityOptimizer

class Tests(unittest.TestCase):
    def test_code_generation(self):
        with tempfile.TemporaryDirectory() as t:
            r=CodeGenerationEngine(Path(t)).run()
            self.assertTrue((Path(r["project"])/"app.py").exists())

    def test_website(self):
        with tempfile.TemporaryDirectory() as t:
            r=WebsiteDeployer(Path(t)).run()
            self.assertTrue((Path(r["site_dir"])/"index.html").exists())

    def test_domain(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(DomainOrchestrator(Path(t)).run()["purchase_status"],"approval_required")

    def test_customer_and_competitor(self):
        with tempfile.TemporaryDirectory() as t:
            h=Path(t)
            self.assertIn("funnel",CustomerAcquisitionV2(h).run())
            self.assertIn("analyses",CompetitorIntelligence(h).run())

    def test_negotiation(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("strategy",NegotiationEngine(Path(t)).run())

    def test_council_and_memory(self):
        with tempfile.TemporaryDirectory() as t:
            h=Path(t)
            self.assertIn(CEOCouncilV2(h).run()["decision"],{"advance","hold"})
            self.assertEqual(MemoryGraph(h).run()["node_count"],0)

    def test_self_evolution(self):
        with tempfile.TemporaryDirectory() as t:
            r=SelfEvolution(Path(t)).run()
            self.assertTrue(Path(r["proposal_file"]).exists())
            self.assertEqual(r["apply_mode"],"reviewed_patch_only")

    def test_profit(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("recommendations",ProfitabilityOptimizer(Path(t)).run())

if __name__=="__main__":
    unittest.main()
