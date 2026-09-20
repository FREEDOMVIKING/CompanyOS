import unittest

from companyos.extensions.generated.marketplace_matching_engine import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class MarketplaceMatchingEngineTests(unittest.TestCase):
    def test_manifest_and_ranked_match(self):
        result = evaluate({
            "buyers": [{
                "id": "b1",
                "name": "Buyer One",
                "category": "software",
                "location": "us",
                "requirements": ["automation"],
                "tags": ["fast"],
                "budget_max": 100,
            }],
            "sellers": [{
                "id": "s1",
                "name": "Seller One",
                "category": "software",
                "location": "us",
                "capabilities": ["automation"],
                "tags": ["fast"],
                "price": 40,
            }],
        })
        self.assertEqual(CAPABILITY_ID, "marketplace_matching_engine")
        self.assertEqual(capability_manifest()["mode"], "pure_analysis")
        self.assertEqual(result["match_count"], 1)
        match = result["ranked_matches"][0]
        self.assertEqual((match["buyer_id"], match["seller_id"]), ("b1", "s1"))
        self.assertEqual(match["status"], "rankable")
        self.assertGreater(match["score"], 0)
        self.assertEqual(match["confidence"], 1.0)

    def test_missing_evidence_is_reported_without_invention(self):
        result = evaluate({"buyers": [{"id": "b"}], "sellers": [{"id": "s"}]})
        match = result["ranked_matches"][0]
        self.assertEqual(match["score"], 0.0)
        self.assertEqual(match["status"], "insufficient_evidence")
        self.assertIn("category", match["missing_evidence"])
        self.assertIn("economic_fit", match["missing_evidence"])

    def test_deterministic_order_and_top_k(self):
        context = {
            "buyers": [{"id": "b2", "category": "x"}, {"id": "b1", "category": "x"}],
            "sellers": [{"id": "s2", "category": "x"}, {"id": "s1", "category": "x"}],
            "top_k": 2,
        }
        first = evaluate(context)
        second = evaluate(context)
        self.assertEqual(first, second)
        self.assertEqual(len(first["ranked_matches"]), 2)
        self.assertEqual(first["ranked_matches"][0]["buyer_id"], "b1")

    def test_invalid_context_type(self):
        with self.assertRaises(TypeError):
            evaluate([])


if __name__ == "__main__":
    unittest.main()
