import hashlib, json
from datetime import datetime, timezone

class ArtifactBuilder:
    def build(self, version, source_digest, metadata=None):
        payload = {
            "version": version,
            "source_digest": source_digest,
            "metadata": metadata or {},
            "built_at": datetime.now(timezone.utc).isoformat()
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return {**payload, "artifact_digest": digest, "status": "built"}
