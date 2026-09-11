import hashlib
class DedupeEvidence:
    """749: suppress duplicate evidence items."""
    def dedupe(self, evidence):
        out, seen = [], set()
        for item in evidence or []:
            key = item.get("url") or item.get("id") or hashlib.sha256(str(item).encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out
