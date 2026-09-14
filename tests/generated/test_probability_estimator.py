import unittest

from companyos.extensions.generated.probability_estimator import CAPABILITY_ID, capability_manifest, evaluate


class ProbabilityEstimatorTests(unittest.TestCase):
    def test_manifest_is_safe_and_analytical(self):
        manifest = capability_manifest()
        self.assertEqual(CAPABILITY_ID, "probability_estimator")
        self.assertEqual(manifest["capability_id"], CAPABILITY_ID)
        self.assertTrue(manifest["safe"])
        self.assertEqual(manifest["side_effects"], [])
        self.assertFalse(manifest["external_actions"])

    def test_uses_candidate_score_and_threshold_deterministically(self):
        context = {
            "candidate_records": [
                {"candidate_id": "a", "score": 30, "threshold": 60},
                {"candidate_id": "b", "score": 45, "threshold": 60},
            ]
        }
        first = evaluate(context)
        second = evaluate(context)
        self.assertEqual(first, second)
        self.assertEqual(first["summary"]["candidate_count"], 2)
        self.assertEqual(first["probability_estimates"][0]["estimated_probability"], 0.5)
        self.assertEqual(first["probability_estimates"][1]["estimated_probability"], 0.75)
        self.assertEqual(first["probability_estimates"][0]["probability_band"], "moderate")
        self.assertEqual(first["probability_estimates"][1]["probability_band"], "high")

    def test_semantic_evidence_fallback_covers_reported_candidates(self):
        context = {
            "compounding_request": {
                "semantic_evidence": {
                    "detail": {
                        "candidate_ids": ["a", "b"],
                        "average_score": 16.17,
                        "average_gap_to_threshold": 43.83,
                    }
                }
            }
        }
        result = evaluate(context)
        self.assertEqual(result["summary"]["candidate_count"], 2)
        self.assertEqual(result["probability_estimates"][0]["threshold"], 60.0)
        self.assertEqual(result["probability_estimates"][0]["estimated_probability"], 0.2695)
        self.assertEqual(result["summary"]["low_probability_count"], 2)
        self.assertTrue(result["planning_guidance"]["analytical_only"])

    def test_gap_can_derive_threshold(self):
        result = evaluate({"candidates": [{"id": "x", "score": 20, "gap": 10}]})
        estimate = result["probability_estimates"][0]
        self.assertEqual(estimate["threshold"], 30.0)
        self.assertEqual(estimate["gap_to_threshold"], 10.0)
        self.assertEqual(estimate["estimated_probability"], round(20 / 30, 6))

    def test_invalid_context_is_rejected(self):
        with self.assertRaises(TypeError):
            evaluate(None)

    def test_empty_context_has_safe_empty_result(self):
        result = evaluate({})
        self.assertEqual(result["probability_estimates"], [])
        self.assertIsNone(result["summary"]["average_estimated_probability"])
        self.assertTrue(result["summary"]["heuristic_warning"])


if __name__ == "__main__":
    unittest.main()
