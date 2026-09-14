import unittest

from companyos.extensions.generated.candidate_gap_ranker import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class CandidateGapRankerTests(unittest.TestCase):
    def test_manifest_identifies_safe_analysis(self):
        manifest = capability_manifest()
        self.assertEqual(CAPABILITY_ID, "candidate_gap_ranker")
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertTrue(manifest["safe"])
        self.assertEqual(manifest["side_effects"], [])

    def test_ranks_common_high_leverage_gap_first(self):
        context = {
            "profit": {
                "qualification_rejections": [
                    {
                        "id": "one",
                        "name": "Alpha",
                        "score": 20,
                        "reasons": [
                            "missing_external_evidence",
                            "missing_executable_next_action",
                        ],
                    },
                    {
                        "id": "two",
                        "name": "Beta",
                        "score": 40,
                        "reasons": ["missing_external_evidence"],
                    },
                ]
            }
        }
        result = evaluate(context)
        self.assertEqual(result["summary"]["candidate_count"], 2)
        self.assertEqual(result["ranked_gaps"][0]["reason"], "missing_external_evidence")
        self.assertEqual(result["ranked_gaps"][0]["candidate_count"], 2)
        self.assertEqual(result["candidate_priority"][0]["id"], "one")

    def test_handles_empty_or_malformed_input(self):
        result = evaluate({"profit": {"qualification_rejections": "invalid"}})
        self.assertEqual(result["summary"]["candidate_count"], 0)
        self.assertEqual(result["ranked_gaps"], [])
        self.assertEqual(result["candidate_priority"], [])

    def test_does_not_mutate_context_and_preserves_unknown_gaps(self):
        context = {
            "profit": {
                "qualification_rejections": [
                    {"id": "x", "reasons": ["new_gap"], "score": "bad"}
                ]
            }
        }
        original = {"profit": {"qualification_rejections": [{"id": "x", "reasons": ["new_gap"], "score": "bad"}]}}
        result = evaluate(context)
        self.assertEqual(context, original)
        self.assertEqual(result["candidate_priority"][0]["unknown_gaps"], ["new_gap"])
        self.assertEqual(result["candidate_priority"][0]["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
