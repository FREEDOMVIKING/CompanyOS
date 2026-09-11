import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


class JsonStore:
    def __init__(self, runtime_dir: Path):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.runtime_dir / name

    def read(self, name: str, default: Any) -> Any:
        path = self.path(name)
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return default

    def write(self, name: str, data: Any) -> Path:
        path = self.path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=path.name, dir=str(path.parent))
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return path

    def append_event(self, event: Dict[str, Any]) -> None:
        events = self.read("executive_events.json", [])
        events.append(event)
        self.write("executive_events.json", events[-2000:])
