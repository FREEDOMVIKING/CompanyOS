class EvidenceNoveltyScore:
    """909: score whether new evidence adds genuinely new information."""
    def score(self, existing, new_items):
        existing=list(existing or [])
        new_items=list(new_items or [])
        existing_keys={e.get("url") or e.get("id") or str(e) for e in existing}
        novel=[e for e in new_items if (e.get("url") or e.get("id") or str(e)) not in existing_keys]
        return {"novel_count":len(novel),"total_new":len(new_items),
                "novelty":round(len(novel)/max(1,len(new_items)),3),"novel":novel}
