import json
from pathlib import Path
from typing import Any

def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError, TypeError):
        return default

def read_jsonl(path: Path, limit: int = 200):
    items = []
    try:
        with Path(path).open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return items[-limit:]
