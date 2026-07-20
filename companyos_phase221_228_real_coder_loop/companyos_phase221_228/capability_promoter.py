from __future__ import annotations
from datetime import datetime,timezone

class CapabilityPromoter:
    """226: register a verified live capability and its provenance."""

    def promote(self,registry,capability,module,mission_id,model_metadata=None):
        record={
            "module":module,
            "verified":True,
            "mission_id":mission_id,
            "built_at":datetime.now(timezone.utc).isoformat(),
            "model_metadata":model_metadata or {},
            "source":"autonomous_real_coder_loop",
        }
        registry.register(capability,record)
        return record
