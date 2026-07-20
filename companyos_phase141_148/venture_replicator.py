from __future__ import annotations
from typing import Any, Dict, List

class VentureReplicator:
    """146: clone proven internal business patterns into new validation tracks."""

    def candidates(self, ventures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for v in ventures:
            traction = float(v.get("traction", 0))
            repeatability = float(v.get("repeatability", 0))
            margin = float(v.get("margin", 0))
            if traction >= .7 and repeatability >= .7 and margin >= .5:
                out.append({
                    "source_venture": v.get("name"),
                    "replication_allowed": True,
                    "mode": "new_internal_validation_track",
                })
        return out
