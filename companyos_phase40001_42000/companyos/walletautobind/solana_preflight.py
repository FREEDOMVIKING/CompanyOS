import json
import os
import urllib.request
from pathlib import Path

class SolanaPreflightValidator:
    def __init__(self, root):
        self.root = Path(root)

    def _rpc(self, method, params=None):
        url = os.getenv("SOLANA_RPC_URL", "").strip()
        if not url:
            return {"success":False,"status":"solana_rpc_missing"}

        payload = {
            "jsonrpc":"2.0",
            "id":1,
            "method":method,
            "params":params or [],
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type":"application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                return {"success":False,"status":"rpc_error","error":data["error"]}
            return {"success":True,"result":data.get("result")}
        except Exception as exc:
            return {"success":False,"status":"rpc_exception","error":type(exc).__name__,"message":str(exc)}

    def validate(self):
        signer = os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip()
        rpc = os.getenv("SOLANA_RPC_URL", "").strip()

        health = self._rpc("getHealth") if rpc else {"success":False,"status":"solana_rpc_missing"}
        blockhash = self._rpc("getLatestBlockhash", [{"commitment":"confirmed"}]) if rpc else {"success":False,"status":"solana_rpc_missing"}

        checks = {
            "solana_rpc_configured": bool(rpc),
            "signer_command_configured": bool(signer),
            "rpc_health_ok": bool(health.get("success")),
            "latest_blockhash_available": bool(blockhash.get("success")),
            "signer_value_exposed": False,
            "broadcast_attempted": False,
        }

        return {
            "passed": all([
                checks["solana_rpc_configured"],
                checks["signer_command_configured"],
                checks["rpc_health_ok"],
                checks["latest_blockhash_available"],
            ]),
            "checks": checks,
            "health": health,
            "latest_blockhash": blockhash,
            "note":"Preflight validates RPC and signer presence only. It does not sign or broadcast a transaction."
        }
