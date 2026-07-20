from __future__ import annotations

class AutonomousGapBuilder:
    """227: choose highest-priority buildable capability gap."""

    def choose(self,gaps):
        buildable=[g for g in gaps if g.get("autonomous_build_candidate",True)]
        buildable.sort(key=lambda x:float(x.get("priority",0)),reverse=True)
        return buildable[0] if buildable else None
