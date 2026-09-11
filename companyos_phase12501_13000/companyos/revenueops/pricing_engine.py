class PricingExperimentEngine:
    def propose(self, base_price, deltas=(-.1,0,.1)):
        return [{"price":round(float(base_price)*(1+d),2),"delta":d,"status":"experiment_candidate"} for d in deltas]
