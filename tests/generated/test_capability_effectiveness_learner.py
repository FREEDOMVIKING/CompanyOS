import unittest

from companyos.extensions.generated.capability_effectiveness_learner import (
    CAPABILITY_ID,
    capability_manifest,
    evaluate,
)


class CapabilityEffectivenessLearnerTests(unittest.TestCase):
    def test_manifest_and_capability_id(self):
        manifest = capability_manifest()
        self.assertEqual(CAPABILITY_ID, "capability_effectiveness_learner")
        self.assertEqual(manifest["id"], CAPABILITY_ID)
        self.assertTrue(manifest["safety"]["pure_analysis_only"])

    def test_compares_reported_metrics_without_fabrication(self):
        result = evaluate(
            {
                "baseline_metrics": {"evidence": 100, "conversion": 50},
                "current_metrics": {"evidence": 120, "conversion": 60},
            }
        )
        self.assertEqual(len(result["comparisons"]), 2)
        self.assertEqual(result["comparisons"][1]["relative_change"], 0.2)
        self.assertEqual(result["comparisons"][0]["absolute_change"], 20)
        self.assertEqual(result["evidence_status"], "reported_only")

    def test_missing_and_non_numeric_values_are_not_invented(self):
        result = evaluate(
            {
                "reported_metrics": [
                    {"name": "evidence", "before": 10, "after": None},
                    {"name": "conversion", "before": 10, "after": 12},
                ]
            }
        )
        self.assertEqual([item["metric"] for item in result["comparisons"]], ["conversion"])
        self.assertEqual(result["unavailable_metrics"], ["evidence"])
        self.assertEqual(result["comparisons"][0]["relative_change"], 0.2)

    def test_zero_baseline_is_explicitly_undefined(self):
        result = evaluate(
            {"before": {"profit": 0}, "after": {"profit": 5}}
        )
        comparison = result["comparisons"][0]
        self.assertIsNone(comparison["relative_change"])
        self.assertEqual(comparison["relative_change_status"], "undefined_zero_baseline")


if __name__ == "__main__":
    unittest.main()
