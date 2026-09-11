class RegionalizationPlanner:
    def adapt(self, market, offer):
        return {
            "market":market,
            "offer":offer,
            "adaptations":{
                "language":market.get("language","default"),
                "currency":market.get("currency","USD"),
                "compliance_review_required":True,
                "local_pricing_test_required":True
            }
        }
