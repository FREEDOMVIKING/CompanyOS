from companyos_phase905_920 import EvidenceNoveltyScore
class NovelEvidenceFilter:
    """924: reject repeated evidence and keep only genuinely novel items."""
    def apply(self, existing, new_items, min_novelty=0.25):
        score=EvidenceNoveltyScore().score(existing,new_items)
        return {
            "accepted":score.get("novel",[]) if score.get("novelty",0)>=min_novelty else [],
            "novelty":score.get("novelty",0),
            "novel_count":score.get("novel_count",0),
            "total_new":score.get("total_new",0),
        }
