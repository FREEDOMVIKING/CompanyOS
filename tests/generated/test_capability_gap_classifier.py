import unittest

from companyos.extensions.generated.capability_gap_classifier import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class CapabilityGapClassifierTests(unittest.TestCase):
    def test_manifest_is_pure_and_identifies_capability(self):
        manifest = capability_manifest()
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertTrue(manifest["pure"])
        self.assertEqual(manifest["side_effects"], [])

    def test_execution_gap_is_ranked_from_explicit_blocker(self):
        context = {
            "findings": [],
            "profit": {
                "qualification_rejections": [
                    {
                        "id": "op-1",
                        "reasons": ["missing_executable_next_action", "probability_unestimated"],
                    }
                ],
                "decision": "research_more",
            },
        }
        result = evaluate(context)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["next_gap"]["id"], "execution_planning")
        self.assertEqual(result["next_gap"]["evidence"][0]["item_id"], "op-1")
        self.assertEqual(result["observed_signals"]["reason_counts"]["probability_unestimated"], 1)

    def test_enrichment_queue_is_used_without_fabricating_a_blocker(self):
        result = evaluate({"findings": [], "profit": {"enrichment_queue_count": 30, "decision": "research_more"}})
        self.assertEqual(result["next_gap"]["id"], "enrichment_pipeline")
        self.assertNotIn("missing_external_evidence", result["observed_signals"]["reason_counts"])
        self.assertEqual(result["next_gap"]["evidence"][0]["path"], "profit.enrichment_queue_count")

    def test_empty_context_reports_insufficient_signal(self):
        result = evaluate({})
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["next_gap"])
        self.assertEqual(result["ranked_gaps"], [])
        self.assertTrue(result["limitations"])

    def test_invalid_input_is_safe(self):
        result = evaluate(None)
        self.assertEqual(result["status"], "invalid_input")
        self.assertIsNone(result["next_gap"])


if __name__ == "__main__":
    unittest.main()
