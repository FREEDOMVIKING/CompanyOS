class EvidenceUpdater:
    """579: merge new evidence without losing prior venture evidence."""

    def merge(self, prior, new):
        prior = dict(prior or {})
        new = dict(new or {})
        merged = dict(prior)
        for key, value in new.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                nested = dict(merged[key])
                nested.update(value)
                merged[key] = nested
            else:
                merged[key] = value
        return merged
