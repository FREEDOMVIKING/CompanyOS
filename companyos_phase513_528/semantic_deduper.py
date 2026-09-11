import re

class SemanticDeduper:
    """514: lightweight token-similarity dedupe for near-duplicate public signals."""

    def _tokens(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        return {
            x for x in re.findall(r"[a-z0-9]+", text)
            if len(x) >= 4
        }

    def similarity(self, a, b):
        ta, tb = self._tokens(a), self._tokens(b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / max(1, len(ta | tb))

    def unique(self, records, threshold=0.72):
        out = []
        for r in records:
            if any(self.similarity(r, x) >= threshold for x in out):
                continue
            out.append(r)
        return out
