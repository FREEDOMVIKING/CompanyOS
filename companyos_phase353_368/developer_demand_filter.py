from __future__ import annotations

class DeveloperDemandFilter:
    """358: retain technology/business signals with engagement or explicit demand."""

    def apply(self, records):
        out = []
        for r in records:
            md = r.get("metadata") or {}
            score = int(md.get("score") or 0)
            comments = int(md.get("comments") or md.get("descendants") or 0)
            if r.get("source") == "GitHub Issues" or score >= 10 or comments >= 5:
                out.append(r)
        return out
