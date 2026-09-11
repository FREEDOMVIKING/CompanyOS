import tempfile, unittest
from pathlib import Path

from companyos.expansion.capabilities import capability_manifest
from companyos.expansion.approvals import ApprovalGate
from companyos.expansion.engine import ExpansionEngine
from companyos.expansion import services

class ExpansionTests(unittest.TestCase):
    def test_all_21_capabilities_present(self):
        manifest = capability_manifest()
        self.assertEqual(len(manifest), 21)
        self.assertEqual(len({x["id"] for x in manifest}), 21)

    def test_approval_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = ApprovalGate(Path(tmp))
            self.assertTrue(gate.evaluate("transfer_funds","high")["approval_required"])
            self.assertFalse(gate.evaluate("internal_analysis","low")["approval_required"])

    def test_internal_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ExpansionEngine(Path(tmp)).execute_internal_demo()
            self.assertIn("opportunity", result)
            self.assertIn("product", result)
            self.assertIn("website", result)
            self.assertIn("campaign", result)
            self.assertIn("company", result)

    def test_finance_interfaces_proposal_only(self):
        bank = services.Banking().transfer_proposal("a","b",100)
        crypto = services.Crypto().transaction_proposal("solana","w","d",1,"SOL")
        self.assertEqual(bank["status"], "approval_required")
        self.assertEqual(crypto["status"], "approval_required")

    def test_document_and_legal(self):
        doc = services.Documents().generate("proposal", {"x":1})
        legal = services.Legal().review("contract","review this")
        self.assertEqual(doc["status"], "generated_draft")
        self.assertEqual(legal["status"], "human_legal_review_required")

    def test_software_factory(self):
        plan = services.SoftwareFactory().build_plan({"name":"app"})
        self.assertIn("tests", plan["pipeline"])
        self.assertIn("security_scan", plan["pipeline"])

    def test_engine_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = ExpansionEngine(Path(tmp)).run_cycle()
            self.assertEqual(r["capability_count"], 21)
            self.assertEqual(r["safety"]["default_external_mode"], "proposal_only")
            self.assertTrue((Path(tmp)/"companyos_runtime"/"expansion21"/"latest_expansion_status.json").exists())

    def test_action_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = ExpansionEngine(Path(tmp))
            a = e.propose("email","send_email",{"to":"x@example.com"},"high")
            self.assertTrue(a["approval_required"])
            self.assertEqual(a["execution_mode"],"proposal_only")

if __name__ == "__main__":
    unittest.main()
