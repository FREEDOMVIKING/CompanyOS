from __future__ import annotations

class OpportunityEvidenceLinker:
    """365: preserve evidence URLs/titles in CEO decision candidates."""

    def link(self, ranked):
        out = []
        for item in ranked:
            opp = item.get("opportunity") or {}
            out.append({
                **item,
                "evidence_links": list(dict.fromkeys(opp.get("evidence", []))),
            })
        return out
