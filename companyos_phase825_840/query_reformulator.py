class QueryReformulator:
    """827: improve queries when evidence quality remains weak."""

    def reformulate(self, query, gaps=None, round_no=1):
        gaps = list(gaps or [])
        suffix = []
        if "demand" in gaps:
            suffix.append("customer demand proof")
        if "pricing" in gaps:
            suffix.append("pricing willingness to pay")
        if "alternatives" in gaps:
            suffix.append("competitors alternatives")
        if "risk" in gaps:
            suffix.append("failure risks")
        if "problem" in gaps:
            suffix.append("customer pain problem")

        if not suffix:
            suffix = ["recent evidence", "commercial intent", "real user demand"]

        return f"{str(query).strip()} {' '.join(suffix)} round {int(round_no)}".strip()
