#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "github_read_config.json"
STATE = MEM / "github_read_state.json"
HEALTH = MEM / "github_read_health.json"
CACHE = MEM / "github_read_cache.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def request_json(endpoint: str) -> tuple[int, Any]:
    cfg = load(CFG, {})
    token_name = cfg.get("token_environment_variable", "GITHUB_TOKEN")
    token = os.getenv(token_name)
    if not token:
        raise RuntimeError(f"{token_name} is not set")

    url = cfg.get("api_base", "https://api.github.com").rstrip("/") + endpoint
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "CompanyOS-ReadConnector"
        },
        method="GET"
    )

    with urllib.request.urlopen(
        req,
        timeout=int(cfg.get("timeout_seconds", 20))
    ) as response:
        return response.status, json.loads(response.read().decode("utf-8"))

def probe() -> dict[str, Any]:
    try:
        code, user = request_json("/user")
        result = {
            "success": code == 200,
            "status": "github_read_connector_ready",
            "authenticated_login": user.get("login"),
            "credential_value_recorded": False
        }
        save(STATE, {
            "generated_at": now(),
            "authenticated_login": user.get("login"),
            "last_probe_status": code
        })
        save(HEALTH, {
            "healthy": code == 200,
            "last_checked_at": now(),
            "http_status": code,
            "credential_value_recorded": False
        })
        return result
    except Exception as exc:
        save(HEALTH, {
            "healthy": False,
            "last_checked_at": now(),
            "error": str(exc),
            "credential_value_recorded": False
        })
        return {
            "success": False,
            "status": "github_read_connector_not_ready",
            "error": str(exc)
        }

def repos(limit: int = 20) -> dict[str, Any]:
    code, data = request_json(
        f"/user/repos?per_page={max(1, min(limit, 100))}&sort=updated"
    )
    rows = [{
        "name": x.get("name"),
        "full_name": x.get("full_name"),
        "private": x.get("private"),
        "updated_at": x.get("updated_at"),
        "default_branch": x.get("default_branch")
    } for x in data]

    result = {
        "success": code == 200,
        "status": "github_repositories_read",
        "count": len(rows),
        "repositories": rows
    }
    save(CACHE, {"generated_at": now(), "repositories": rows})
    return result

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "github_read_status",
        "config": load(CFG, {}),
        "state": load(STATE, {}),
        "health": load(HEALTH, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "probe":
            result = probe()
        elif action == "repos":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            result = repos(limit)
        elif action == "status":
            result = status()
        else:
            result = {
                "success": False,
                "status": "unknown_action",
                "allowed": ["probe", "repos [limit]", "status"]
            }
    except Exception as exc:
        result = {
            "success": False,
            "status": "github_read_error",
            "error": str(exc)
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
