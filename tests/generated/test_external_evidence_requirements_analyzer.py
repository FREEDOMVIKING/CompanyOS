import unittest

from companyos.extensions.generated.external_evidence_requirements_analyzer import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class ExternalEvidenceRequirementsAnalyzerTests(unittest.TestCase):
    def test_manifest_is_safe_and_analytical(self):
        manifest = capability_manifest()
        self.assertEqual(manifest["capability_id"], CAPABILITY_ID)
        self.assertEqual(manifest["kind"], "analytical")
        self.assertTrue(manifest["safe"])
        self.assertEqual(manifest["side_effects"], [])
        self.assertFalse(manifest["external_actions"])

    def test_generates_deterministic_guidance_for_candidates(self):
        context = {
            "gap_id": "semantic-example",
            "source_capability": "candidate_gap_ranker_downstream_gap_detector",
            "semantic_evidence": {
                "reason": "missing_external_evidence",
                "detail": {"affected_candidates": 2, "candidate_ids": ["b", "a"]},
            },
            "candidate_records": {
                "a": {"evidence": [{"reference": "internal-record-1"}]},
                "b": {},
            },
        }
        first = evaluate(context)
        second = evaluate(context)
        self.assertEqual(first, second)
        self.assertEqual(first["summary"]["affected_candidates"], 2)
        self.assertEqual(first["summary"]["evidence_records_observed"], 1)
        self.assertEqual(len(first["evidence_requirements"]), 6)
        self.assertEqual(first["candidate_guidance"][0]["candidate_id"], "b")
        self.assertFalse(first["candidate_guidance"][0]["external_retrieval_performed"])
        self.assertEqual(first["candidate_guidance"][1]["evidence_state"], "evidence_reference_observed")

    def test_handles_missing_and_malformed_context_without_side_effects(self):
        result = evaluate({"compounding_request": {"gap_id": "g"}, "candidate_ids": ["x", "x", ""]})
        self.assertEqual(result["gap_id"], "g")
        self.assertEqual(result["candidate_guidance"][0]["candidate_id"], "x")
        self.assertEqual(result["summary"]["candidate_ids_provided"], 1)
        self.assertEqual(result["summary"]["evidence_records_observed"], 0)
        self.assertFalse(result["summary"]["external_retrieval_performed"])
        self.assertFalse(result["summary"]["decision_or_approval_made"])


if __name__ == "__main__":
    unittest.main()