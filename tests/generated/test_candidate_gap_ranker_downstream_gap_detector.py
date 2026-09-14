import unittest

from companyos.extensions.generated.candidate_gap_ranker_downstream_gap_detector import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class CandidateGapRankerDownstreamGapDetectorTests(unittest.TestCase):
    def test_manifest_is_safe_and_analytical(self):
        manifest = capability_manifest()
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertEqual(manifest["kind"], "analytical")
        self.assertTrue(manifest["safe"])
        self.assertEqual(manifest["side_effects"], [])

    def test_detects_concentrated_bottleneck(self):
        context = {
            "profit": {
                "execution_threshold": 60,
                "qualification_rejections": [
                    {"id": "a", "score": 30, "reasons": ["missing_external_evidence", "probability_unestimated"]},
                    {"id": "b", "score": 40, "reasons": ["missing_external_evidence"]},
                    {"id": "c", "score": 70, "reasons": ["missing_executable_next_action"]},
                ],
            }
        }
        result = evaluate(context)
        self.assertEqual(result["top_bottleneck"]["reason"], "missing_external_evidence")
        self.assertEqual(result["top_bottleneck"]["affected_candidates"], 2)
        self.assertEqual(result["top_bottleneck"]["average_gap_to_threshold"], 25.0)
        self.assertTrue(result["top_bottleneck"]["unresolved"])

    def test_reads_ranker_output_and_does_not_mutate_input(self):
        context = {"candidate_gap_ranker": {"ranked_gaps": [
            {"candidate_id": "x", "score": 20, "reasons": ["probability_unestimated"]}
        ]}}
        before = {"candidate_gap_ranker": {"ranked_gaps": [
            {"candidate_id": "x", "score": 20, "reasons": ["probability_unestimated"]}
        ]}}
        evaluate(context)
        self.assertEqual(context, before)
        self.assertEqual(evaluate(context)["top_bottleneck"]["reason"], "probability_unestimated")

    def test_empty_input_is_explicit(self):
        result = evaluate({})
        self.assertEqual(result["bottlenecks"], [])
        self.assertIsNone(result["top_bottleneck"])
        self.assertFalse(result["source_observed"])


if __name__ == "__main__":
    unittest.main()
