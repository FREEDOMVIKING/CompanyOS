from .freshness_score import FreshnessScore
from .credibility_score import CredibilityScore
class ResearchNormalizer:
    """758: normalize raw evidence into comparable scored records."""
    def normalize(self, evidence):
        out=[]
        for item in evidence or []:
            row=dict(item)
            freshness=FreshnessScore().score(row)
            credibility=CredibilityScore().score(row)
            row["freshness_score"]=freshness
            row["credibility_score"]=credibility
            row["evidence_score"]=round((freshness*0.35)+(credibility*0.65),3)
            out.append(row)
        return out
