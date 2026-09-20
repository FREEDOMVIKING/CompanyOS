import unittest

from companyos.extensions.generated.marketplace_liquidity_analyzer import CAPABILITY_ID, capability_manifest, evaluate


class MarketplaceLiquidityAnalyzerTests(unittest.TestCase):
    def test_manifest(self):
        manifest = capability_manifest()
        self.assertEqual(CAPABILITY_ID, "marketplace_liquidity_analyzer")
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertTrue(manifest["pure"])

    def test_empty_context_is_explicitly_insufficient(self):
        result = evaluate({})
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["segments"], [])
        self.assertEqual(result["summary"]["confidence"], 0.0)

    def test_demand_heavy_segment(self):
        result = evaluate({"observations": [{"segment": "tools", "supply": 10, "demand": 30, "transactions": 4, "source": "survey-a"}]})
        segment = result["segments"][0]
        self.assertEqual(segment["balance"], "demand_heavy")
        self.assertEqual(segment["unmet_demand"], 20.0)
        self.assertGreater(segment["opportunity_score"], 0)
        self.assertEqual(result["evidence_quality"]["transaction_coverage"], 1.0)

    def test_invalid_rows_are_not_fabricated(self):
        result = evaluate({"observations": [{"segment": "bad", "supply": -2, "demand": 4}, {"segment": "good", "supply": 2, "demand": 2}]})
        self.assertEqual(len(result["segments"]), 1)
        self.assertEqual(result["segments"][0]["segment"], "good")

    def test_input_is_not_mutated(self):
        context = {"supply": 2, "demand": 5}
        before = dict(context)
        evaluate(context)
        self.assertEqual(context, before)


if __name__ == "__main__":
    unittest.main()
