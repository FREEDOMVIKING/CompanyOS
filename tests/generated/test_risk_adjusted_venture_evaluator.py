import unittest
from companyos.extensions.generated.risk_adjusted_venture_evaluator import CAPABILITY_ID, capability_manifest, evaluate


class RiskAdjustedVentureEvaluatorTests(unittest.TestCase):
    def test_contract(self):
        self.assertEqual(CAPABILITY_ID, "risk_adjusted_venture_evaluator")
        self.assertEqual(capability_manifest()["id"], CAPABILITY_ID)

    def test_confidence_weighted_profit_and_unknowns(self):
        result = evaluate({
            "pricing": {"price": {"value": 100, "confidence": 0.8}},
            "operating_assumptions": {"customers": {"value": 10, "confidence": 0.5}, "fixed_cost": 200},
        })
        known = result["scenarios"]["known"]
        self.assertEqual(known["reasons"], ["fit_unestimated"])
        self.assertEqual(known["profit"], 800.0)
        self.assertEqual(result["unknowns"], ["fit_unestimated"])

    def test_missing_inputs_are_not_fabricated(self):
        result = evaluate({"business_model_fit": {"value": 0.7, "confidence": 0.9}})
        self.assertIsNone(result["scenarios"]["known"]["profit"])
        self.assertEqual(result["unknowns"], ["inputs_unknown"])

    def test_explicit_success_probability(self):
        result = evaluate({"price": 50, "units": 4, "fixed_cost": 20, "success_probability": 0.5, "business_model_fit": 0.6})
        self.assertEqual(result["scenarios"]["known"]["realized_profit"], 90.0)
        self.assertEqual(result["unknowns"], [])


if __name__ == "__main__":
    unittest.main()
