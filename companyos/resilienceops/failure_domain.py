class FailureDomainAnalyzer:
    def analyze(self, services):
        domains={}
        for s in services or []:
            d=s.get("failure_domain","default")
            domains.setdefault(d,[]).append(s.get("name"))
        return {
            "domains":domains,
            "single_domain_risk":len(domains)<=1 and bool(services)
        }
