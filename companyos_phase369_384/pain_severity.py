from __future__ import annotations

class PainSeverity:
    """373: estimate severity from cost/time/failure language and repetition."""

    HIGH = ("critical","blocking","broken","hours","expensive","cannot","impossible","urgent")
    MED = ("slow","manual","difficult","frustrating","repetitive","error")

    def score(self, cluster):
        text = " ".join(str(r.get("text","")) for r in cluster.get("records", [])).lower()
        score = 3 + min(3, int(cluster.get("count",0)))
        score += min(2, sum(1 for t in self.HIGH if t in text))
        score += min(2, sum(1 for t in self.MED if t in text))
        return min(10, score)
