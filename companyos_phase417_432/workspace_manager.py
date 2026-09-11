from pathlib import Path
import json

class WorkspaceManager:
    """419: isolated workspace per venture."""

    def __init__(self, root):
        self.root = Path(root)

    def create(self, venture_id, packet):
        path = self.root / ".companyos_runtime" / "ventures" / venture_id
        for d in ("workspace","artifacts","reports","state"):
            (path / d).mkdir(parents=True, exist_ok=True)
        (path / "state" / "venture_packet.json").write_text(
            json.dumps(packet, indent=2, default=str), encoding="utf-8"
        )
        return str(path)
