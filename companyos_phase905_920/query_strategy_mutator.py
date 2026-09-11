class QueryStrategyMutator:
    """907: generate materially different queries after stagnation."""
    def mutate(self, base_query, causes, round_no):
        reasons=set((causes or {}).get("reasons",[]))
        parts=[str(base_query or "").strip()]
        if "weak_problem_evidence" in reasons:
            parts += ["complaints","pain frequency","manual workaround","cost of problem"]
        if "weak_pricing_evidence" in reasons:
            parts += ["budget","purchase intent","price accepted","paid alternatives"]
        if "low_source_diversity" in reasons:
            parts += ["forum","review","official documentation","case study"]
        parts += [f"strategy round {int(round_no)}"]
        return " ".join([p for p in parts if p])
