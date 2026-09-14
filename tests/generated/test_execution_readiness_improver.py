import unittest

from companyos.extensions.generated.execution_readiness_improver import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class ExecutionReadinessImproverTests(unittest.TestCase):
    def make_context(self, detail=None, priority=84):
        return {
            "compounding_request": {
                "priority": priority,
                "semantic_evidence": {"detail": detail or {}},
            }
        }

    def test_manifest_is_safe_and_analytical(self):
        manifest = capability_manifest()
        self.assertEqual(CAPABILITY_ID, "execution_readiness_improver")
        self.assertEqual(manifest["kind"], "analytical")
        self.assertTrue(manifest["safe"])
        self.assertEqual(manifest["side_effects"], [])
        self.assertFalse(manifest["execution_allowed"])
        self.assertFalse(manifest["external_action_allowed"])

    def test_material_gap_produces_deterministic_internal_guidance(self):
        detail = {
            "affected_candidates": 7,
            "average_gap_to_threshold": 43.83,
            "average_score": 16.17,
            "candidate_ids": ["a", "b", "a"],
            "reason": "score_below_execution_threshold",
            "unresolved": True,
        }
        result = evaluate(self.make_context(detail))
        self.assertEqual(result["readiness_assessment"]["classification"], "not_ready")
        self.assertEqual(result["readiness_assessment"]["gap_to_threshold"], 43.83)
        self.assertEqual(result["planning_guidance"]["priority"], 84)
        self.assertEqual(result["evidence_summary"]["candidate_ids"], ["a", "b"])
        self.assertFalse(result["constraints"]["execution_performed"])
        self.assertFalse(result["constraints"]["approval_or_deployment_state_changed"])

    def test_nearly_ready_and_ready_classifications(self):
        nearly = evaluate(self.make_context({"average_score": 52, "execution_threshold": 60}))
        ready = evaluate(self.make_context({"average_score": 60, "execution_threshold": 60}))
        self.assertEqual(nearly["readiness_assessment"]["classification"], "nearly_ready")
        self.assertEqual(ready["readiness_assessment"]["classification"], "ready")
        self.assertEqual(ready["planning_guidance"]["actions"][0], "confirm_readiness_evidence")

    def test_missing_or_malformed_input_is_safe_and_repeatable(self):
        first = evaluate(None)
        second = evaluate(None)
        self.assertEqual(first, second)
        self.assertEqual(first["readiness_assessment"]["classification"], "not_ready")
        self.assertEqual(first["evidence_summary"]["candidate_ids"], [])
        self.assertTrue(first["constraints"]["analysis_only"])


if __name__ == "__main__":
    unittest.main()
