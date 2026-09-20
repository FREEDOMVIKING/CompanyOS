import unittest

from companyos.extensions.generated.service_offer_ranker import CAPABILITY_ID, capability_manifest, evaluate


class ServiceOfferRankerTests(unittest.TestCase):
    def test_manifest_and_capability_id(self):
        self.assertEqual(CAPABILITY_ID, "service_offer_ranker")
        self.assertEqual(capability_manifest()["id"], CAPABILITY_ID)

    def test_complete_offers_are_ranked(self):
        result = evaluate({"services": [
            {"name": "Fast urgent", "urgency": 5, "price": 100, "labor_intensity": 1, "sales_friction": 1},
            {"name": "Slow heavy", "urgency": 1, "price": 50, "labor_intensity": 5, "sales_friction": 5},
        ]})
        self.assertEqual(len(result["ranked"]), 2)
        self.assertEqual(result["ranked"][0]["name"], "Fast urgent")
        self.assertEqual(result["ranked"][0]["rank"], 1)

    def test_missing_dimensions_are_not_fabricated(self):
        result = evaluate({"offers": [
            {"name": "Partially specified", "urgency": 4, "price": 125},
        ]})
        self.assertEqual(result["unranked"][0]["missing_dimensions"], ["labor_intensity", "sales_friction"])
        self.assertEqual(result["ranked"], [])

    def test_aliases_are_accepted_without_inventing_values(self):
        result = evaluate({"service_offers": [
            {"title": "Aliased", "urgency_score": 80, "price_usd": 200, "labor": 20, "sales_friction_score": 10},
        ]})
        self.assertEqual(len(result["ranked"]), 1)
        self.assertEqual(result["ranked"][0]["name"], "Aliased")

    def test_invalid_values_are_not_ranked(self):
        result = evaluate({"items": [
            {"name": "Invalid", "urgency": "unknown", "price": 20, "labor_intensity": 2, "sales_friction": 2},
        ]})
        self.assertEqual(result["unranked"][0]["invalid_dimensions"], ["urgency"])
        self.assertEqual(result["ranked"], [])

    def test_empty_context_is_safe(self):
        result = evaluate({})
        self.assertEqual(result["ranked"], [])
        self.assertEqual(result["unranked"], [])


if __name__ == "__main__":
    unittest.main()