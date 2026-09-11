from __future__ import annotations
from .noise_filter import NoiseFilter
from .semantic_clusterer import SemanticClusterer
from .cross_source_agreement import CrossSourceAgreement
from .customer_identifier import CustomerIdentifier
from .pain_severity import PainSeverity
from .frequency_estimator import FrequencyEstimator
from .willingness_to_pay import WillingnessToPay
from .replacement_analyzer import ReplacementAnalyzer
from .business_model_generator import BusinessModelGenerator
from .startup_estimator import StartupEstimator
from .time_to_revenue import TimeToRevenue
from .descriptive_namer import DescriptiveNamer
from .thesis_builder import MarketThesisBuilder
from .investment_decision import InvestmentDecision

class OpportunityIntelligenceCycle:
    """383: public evidence -> semantic clusters -> market theses -> CEO decisions."""

    def __init__(self):
        self.noise = NoiseFilter()
        self.clusterer = SemanticClusterer()
        self.agreement = CrossSourceAgreement()
        self.customer = CustomerIdentifier()
        self.severity = PainSeverity()
        self.frequency = FrequencyEstimator()
        self.wtp = WillingnessToPay()
        self.replacement = ReplacementAnalyzer()
        self.models = BusinessModelGenerator()
        self.startup = StartupEstimator()
        self.revenue = TimeToRevenue()
        self.namer = DescriptiveNamer()
        self.thesis_builder = MarketThesisBuilder()
        self.decision = InvestmentDecision()

    def run(self, records):
        filtered = self.noise.apply(records)
        clusters = self.clusterer.cluster(filtered["accepted"])
        theses = []

        for cluster in clusters:
            theme = cluster["theme"]
            customer = self.customer.identify(cluster)
            startup = self.startup.estimate(theme)

            item = {
                "name": self.namer.name(theme),
                "customer": customer,
                "problem": f"Repeated evidence of {theme.replace('_',' ')} pain.",
                "agreement": self.agreement.score(cluster),
                "pain_severity": self.severity.score(cluster),
                "problem_frequency": self.frequency.score(cluster),
                "willingness_to_pay": self.wtp.score(cluster),
                "replacement_analysis": self.replacement.analyze(cluster),
                "business_model": self.models.generate(customer, theme),
                "startup_estimate": startup,
                "time_to_revenue": self.revenue.estimate(startup),
                "evidence_links": list(dict.fromkeys(
                    r.get("url") for r in cluster.get("records", []) if r.get("url")
                )),
            }

            thesis = self.thesis_builder.build(item)
            thesis["investment"] = self.decision.decide(thesis)
            theses.append(thesis)

        theses.sort(key=lambda x: x["investment"]["investment_score"], reverse=True)

        return {
            "success": True,
            "status": "opportunity_intelligence_completed",
            "records_received": len(records),
            "records_accepted": len(filtered["accepted"]),
            "records_rejected_as_noise": len(filtered["rejected"]),
            "cluster_count": len(clusters),
            "market_theses": theses,
            "top_thesis": theses[0] if theses else None,
        }
