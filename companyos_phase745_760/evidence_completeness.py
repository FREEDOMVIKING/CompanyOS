class EvidenceCompleteness:
    """752: ensure research packets cover minimum decision dimensions."""
    REQUIRED = ("problem","demand","alternatives","pricing","risk")
    def evaluate(self, evidence):
        covered=set()
        for item in evidence or []:
            for tag in item.get("tags",[]):
                covered.add(tag)
        missing=[x for x in self.REQUIRED if x not in covered]
        return {"complete": not missing, "missing": missing, "covered": sorted(covered)}
