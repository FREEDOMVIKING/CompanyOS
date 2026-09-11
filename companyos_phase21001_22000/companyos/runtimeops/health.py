import os, time
from pathlib import Path

class RuntimeHealth:
    def __init__(self, root):
        self.root = Path(root)

    def snapshot(self):
        runtime = self.root / ".companyos_runtime"
        return {
            "runtime_exists": runtime.exists(),
            "reasoning_env_present": (runtime / "live_intelligence.env").exists(),
            "timestamp": time.time(),
            "pid": os.getpid(),
        }
