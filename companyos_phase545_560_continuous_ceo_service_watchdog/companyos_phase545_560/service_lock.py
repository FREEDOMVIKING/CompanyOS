import os
from pathlib import Path

class ServiceLock:
    """552: prevent duplicate CEO service instances."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_service.lock"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self):
        if self.path.exists():
            try:
                pid = int(self.path.read_text().strip())
                os.kill(pid, 0)
                return {"acquired":False,"pid":pid,"reason":"service_already_running"}
            except Exception:
                try:
                    self.path.unlink()
                except Exception:
                    pass
        self.path.write_text(str(os.getpid()), encoding="utf-8")
        return {"acquired":True,"pid":os.getpid()}

    def release(self):
        try:
            if self.path.exists():
                self.path.unlink()
        except Exception:
            pass
