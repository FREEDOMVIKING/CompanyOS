from .hypothesis_builder import HypothesisBuilder
from .validation_budget import ValidationBudget
from .experiment_designer import ExperimentDesigner
from .landing_page_spec import LandingPageSpec
from .offer_builder import OfferBuilder
from .pricing_test import PricingTest
from .demand_thresholds import DemandThresholds

class ValidationOrchestrator:
    """398: create a full validation packet from a market thesis."""

    def __init__(self):
        self.hypothesis = HypothesisBuilder()
        self.budget = ValidationBudget()
        self.experiments = ExperimentDesigner()
        self.page = LandingPageSpec()
        self.offer = OfferBuilder()
        self.pricing = PricingTest()
        self.thresholds = DemandThresholds()

    def plan(self, thesis):
        return {
            "success": True,
            "status": "validation_plan_ready",
            "thesis_name": thesis.get("name"),
            "hypotheses": self.hypothesis.build(thesis),
            "budget": self.budget.limits(),
            "experiments": self.experiments.design(thesis),
            "landing_page_spec": self.page.build(thesis),
            "offer": self.offer.build(thesis),
            "pricing_test": self.pricing.create(thesis),
            "thresholds": self.thresholds.defaults(),
            "full_product_build_required": False,
        }
