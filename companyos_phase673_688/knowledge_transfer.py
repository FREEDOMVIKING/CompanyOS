class KnowledgeTransfer:
    """677: identify reusable lessons across ventures."""

    def transfer(self, source, target):
        reusable = []
        for item in source.get("lessons",[]):
            if item not in target.get("lessons",[]):
                reusable.append(item)
        return {
            "from_venture":source.get("venture_id"),
            "to_venture":target.get("venture_id"),
            "reusable_lessons":reusable,
        }
