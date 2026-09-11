from __future__ import annotations

from pathlib import Path
import os
import sys


def ensure_project_root() -> Path:
    """
    Make direct execution from ~/companyos/tools reliable without requiring
    PYTHONPATH="$PWD".
    """
    here = Path(__file__).resolve()
    candidates = [
        Path.cwd(),
        here.parents[2] if len(here.parents) >= 3 else Path.cwd(),
        Path.home() / "companyos",
    ]

    for root in candidates:
        if (root / "companyos").is_dir():
            s = str(root)
            if s not in sys.path:
                sys.path.insert(0, s)
            return root

    raise RuntimeError("companyos_project_root_not_found")


def load_dotenv(root: Path | None = None) -> Path:
    root = root or ensure_project_root()
    env_path = root / ".env"
    if not env_path.exists():
        raise RuntimeError(f"env_missing:{env_path}")

    for line in env_path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

    return env_path
