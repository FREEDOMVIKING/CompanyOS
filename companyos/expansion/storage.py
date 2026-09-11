import json, os, tempfile
from pathlib import Path
from typing import Any

def read_json(path: Path, default: Any):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default

def write_json(path: Path, data: Any):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def append_json(path: Path, item: Any, limit: int = 5000):
    rows = read_json(path, [])
    if not isinstance(rows, list):
        rows = []
    rows.append(item)
    write_json(path, rows[-limit:])
