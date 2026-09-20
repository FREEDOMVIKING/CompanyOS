import unittest

from companyos.extensions.generated.app_problem_ranker import CAPABILITY_ID, capability_manifest, evaluate


class AppProblemRankerTests(unittest.TestCase):
    def test_manifest_is_safe_and_identified(self):
        manifest = capability_manifest()
        self.assertEqual(CAPABILITY_ID, "app_problem_ranker")
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertTrue(manifest["pure"])
        self.assertFalse(manifest["safety"]["network"])
        self.assertFalse(manifest["safety"]["file_writes"])

    def test_ranks_by_weighted_evidence_and_inverts_competition(self):
        result = evaluate({
            "problems": [
                {"id": "a", "name": "High pain", "pain": 10, "frequency": 10, "price": 10, "competition": 2},
                {"id": "b", "name": "Low pain", "pain": 8, "frequency": 8, "price": 8, "competition": 10},
            ]
        })
        self.assertEqual(result["ranked_problems"][0]["problem_id"], "a")
        self.assertEqual(result["counts"], {"input": 2, "ranked": 2, "unscored": 0})
        self.assertEqual(result["ranked_problems"][0]["evidence_status"], "complete")

    def test_missing_values_are_not_fabricated(self):
        result = evaluate({"candidates": [{"id": "x", "title": "Unknown", "pain": 7}]})
        record = result["ranked_problems"][0]
        self.assertIsNone(record["dimensions"]["frequency"])
        self.assertEqual(record["evidence_status"], "partial")
        self.assertEqual(record["rank_score"], 70.0)

    def test_no_numeric_evidence_is_unscored(self):
        result = evaluate({"problems": [{"id": "x", "name": "No evidence"}]})
        self.assertEqual(result["ranked_problems"], [])
        self.assertEqual(result["unscored_problems"][0]["evidence_status"], "insufficient")

    def test_invalid_context_is_safe(self):
        result = evaluate(None)
        self.assertEqual(result["ranked_problems"], [])
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
