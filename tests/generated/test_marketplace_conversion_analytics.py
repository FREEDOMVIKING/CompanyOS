import unittest

from companyos.extensions.generated.marketplace_conversion_analytics import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class MarketplaceConversionAnalyticsTests(unittest.TestCase):
    def test_manifest_declares_pure_safe_capability(self):
        manifest = capability_manifest()
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertTrue(manifest["safety"]["pure"])
        self.assertFalse(manifest["safety"]["network"])
        self.assertFalse(manifest["safety"]["filesystem"])

    def test_calculates_explicitly_linked_funnel(self):
        result = evaluate(
            {
                "listings": [{"id": "l1"}, {"id": "l2"}, {"id": "l3"}],
                "inquiries": [
                    {"id": "i1", "listing_id": "l1"},
                    {"id": "i2", "listing_id": "l1"},
                    {"id": "i3", "listing_id": "l2"},
                ],
                "transactions": [
                    {"id": "t1", "inquiry_id": "i1"},
                ],
            }
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["metrics"]["listing_to_inquiry"]["numerator"], 2)
        self.assertEqual(result["metrics"]["listing_to_inquiry"]["denominator"], 3)
        self.assertAlmostEqual(result["metrics"]["inquiry_to_transaction"]["rate"], 1 / 3)
        self.assertEqual(result["funnel"]["transactions"], 1)

    def test_does_not_fabricate_orphan_attribution(self):
        result = evaluate(
            {
                "listings": [{"id": "l1"}],
                "inquiries": [
                    {"id": "i1", "listing_id": "missing"},
                    {"id": "i2", "listing_id": "l1"},
                ],
                "transactions": [
                    {"id": "t1", "inquiry_id": "missing"},
                    {"id": "t2", "inquiry_id": "i2"},
                ],
            }
        )
        self.assertEqual(result["funnel"], {"listings": 1, "inquiries": 1, "transactions": 1})
        self.assertEqual(result["metrics"]["listing_to_inquiry"]["numerator"], 1)
        self.assertEqual(result["metrics"]["inquiry_to_transaction"]["numerator"], 1)
        self.assertEqual(result["data_quality"]["orphan_inquiries"], 1)
        self.assertEqual(result["data_quality"]["unattributed_transactions"], 1)

    def test_missing_evidence_uses_null_rates(self):
        result = evaluate({"listings": [], "inquiries": [], "transactions": []})
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIsNone(result["metrics"]["listing_to_inquiry"]["rate"])
        self.assertIsNone(result["metrics"]["inquiry_to_transaction"]["rate"])

    def test_duplicate_ids_are_counted_once(self):
        result = evaluate(
            {
                "listings": [{"id": "l1"}, {"id": "l1"}],
                "inquiries": [{"id": "i1", "listing_id": "l1"}],
                "transactions": [
                    {"id": "t1", "inquiry_id": "i1"},
                    {"id": "t1", "inquiry_id": "i1"},
                ],
            }
        )
        self.assertEqual(result["funnel"], {"listings": 1, "inquiries": 1, "transactions": 1})
        self.assertEqual(result["data_quality"]["duplicate_ids"], 2)

    def test_non_mapping_context_is_safe(self):
        result = evaluate(None)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertIsNone(result["metrics"]["listing_to_inquiry"]["rate"])


if __name__ == "__main__":
    unittest.main()
