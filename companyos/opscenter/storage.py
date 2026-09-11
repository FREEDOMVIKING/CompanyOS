import json
import os
import tempfile
from pathlib import Path
from typing import Any

def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError, TypeError):
        return default

def atomic_write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def append_json(path: Path, item: Any, limit: int = 2000) -> None:
    rows = read_json(path, [])
    if not isinstance(rows, list):
        rows = []
    rows.append(item)
    atomic_write_json(path, rows[-limit:])
