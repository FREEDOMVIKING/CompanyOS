from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path


class ConnectorReadinessAudit:
    """
    Non-destructive readiness audit. It never prints credential values and
    never sends money, email, deployments, or external writes.
    """

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "connector_readiness.json"

    @staticmethod
    def _env_any(*names):
        return any(bool(os.getenv(name, "").strip()) for name in names)

    def _files_matching(self, *keywords):
        matches = []
        lowered = tuple(k.lower() for k in keywords)
        for base in (
            self.root / "companyos",
            self.root / "connectors",
            self.root / "walletintegration",
        ):
            if not base.exists():
                continue
            for p in base.rglob("*.py"):
                s = str(p.relative_to(self.root)).lower()
                if any(k in s for k in lowered):
                    matches.append(str(p.relative_to(self.root)))
                    if len(matches) >= 30:
                        return matches
        return matches

    def _git_remote(self):
        try:
            remote = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                cwd=self.root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            return {"configured": bool(remote), "remote": remote}
        except Exception:
            return {"configured": False, "remote": None}

    def run(self):
        openai_modules = self._files_matching("openai", "provider")
        hosting_modules = self._files_matching("vercel", "hosting", "deploy")
        email_modules = self._files_matching("smtp", "email", "communications")
        wallet_modules = self._files_matching("wallet", "solana", "treasury")

        connectors = {
            "openai": {
                "configured": self._env_any("OPENAI_API_KEY"),
                "adapter_code_present": bool(openai_modules),
                "modules": openai_modules[:8],
            },
            "hosting": {
                "configured": self._env_any(
                    "VERCEL_TOKEN",
                    "CLOUDFLARE_API_TOKEN",
                    "NETLIFY_AUTH_TOKEN",
                ),
                "adapter_code_present": bool(hosting_modules),
                "modules": hosting_modules[:8],
            },
            "email": {
                "configured": (
                    self._env_any("SMTP_HOST")
                    and self._env_any("SMTP_USERNAME", "SMTP_USER")
                    and self._env_any("SMTP_PASSWORD", "SMTP_PASS")
                ),
                "adapter_code_present": bool(email_modules),
                "modules": email_modules[:8],
            },
            "github": {
                **self._git_remote(),
                "adapter_code_present": True,
            },
            "solana_wallet": {
                "configured": (
                    self._env_any("SOLANA_RPC_URL", "RPC_URL")
                    and self._env_any(
                        "SOLANA_PRIVATE_KEY",
                        "PHANTOM_PRIVATE_KEY",
                        "WALLET_PRIVATE_KEY",
                    )
                ),
                "adapter_code_present": bool(wallet_modules),
                "modules": wallet_modules[:8],
                "live_finance_enabled": (
                    os.getenv("COMPANYOS_ENABLE_LIVE_FINANCE", "0") == "1"
                ),
            },
        }

        required_for_core = ["github"]
        core_external_ready = all(
            connectors[name]["configured"] for name in required_for_core
        )

        configured_count = sum(
            1 for value in connectors.values() if value.get("configured")
        )

        result = {
            "checked_at_unix": time.time(),
            "connectors": connectors,
            "configured_count": configured_count,
            "total_count": len(connectors),
            "core_external_ready": core_external_ready,
            "note": (
                "Unconfigured optional connectors do not block the local "
                "autonomous runtime. They block only the external actions "
                "that depend on them."
            ),
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return result
