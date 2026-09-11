from __future__ import annotations

class CustomerIdentifier:
    """372: infer likely customer segment from cluster vocabulary."""

    RULES = [
        (("contractor","construction","estimate","bid"), "small and mid-sized contractors"),
        (("developer","api","github","integration"), "software teams and developers"),
        (("invoice","bookkeeping","accounting"), "small businesses and finance teams"),
        (("support","ticket","customer service"), "customer support teams"),
        (("schedule","dispatch","field service"), "field-service businesses"),
        (("compliance","audit","documentation"), "regulated small and mid-sized businesses"),
    ]

    def identify(self, cluster):
        text = " ".join(
            f"{r.get('title','')} {r.get('text','')}"
            for r in cluster.get("records", [])
        ).lower()
        for terms, customer in self.RULES:
            if any(t in text for t in terms):
                return customer
        return "business users experiencing the repeated workflow pain"
