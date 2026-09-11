class MissionReprioritizer:
    """504: raise priority for ready, evidence-rich, low-failure missions."""

    def apply(self, missions):
        out = []
        for m in missions:
            item = dict(m)
            score = float(item.get("priority",0.5))
            if not item.get("blocked_on"):
                score += 0.1
            score -= min(0.3, int(item.get("attempts",0)) * 0.05)
            item["priority"] = round(max(0, min(1.0, score)), 3)
            out.append(item)
        return sorted(out, key=lambda x:x["priority"], reverse=True)
