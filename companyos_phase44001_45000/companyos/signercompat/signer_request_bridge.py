import json, os, shlex, subprocess
from .sanitized_diagnostics import SanitizedDiagnostics

class SignerRequestBridge:
    def __init__(self):
        self.sanitize = SanitizedDiagnostics().sanitize

    def _run(self, payload):
        cmd = os.getenv("MULTICHAIN_SIGNER_COMMAND", "").strip()
        if not cmd:
            return {"success":False,"status":"signer_command_missing"}

        try:
            p = subprocess.run(
                shlex.split(cmd),
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=30,
            )
            stdout = (p.stdout or "").strip()
            stderr = (p.stderr or "").strip()

            parsed = None
            if stdout:
                try:
                    parsed = json.loads(stdout)
                except Exception:
                    parsed = {"raw": stdout[:2000]}

            return {
                "success": p.returncode == 0,
                "status": "signer_bridge_call_complete" if p.returncode == 0 else "signer_bridge_call_failed",
                "returncode": p.returncode,
                "result": parsed,
                "stderr": stderr[:2000] if stderr else "",
            }
        except Exception as exc:
            return {
                "success":False,
                "status":"signer_bridge_exception",
                "error":type(exc).__name__,
                "message":str(exc),
            }

    def compatibility_probe(self):
        probes = [
            {"action":"status"},
            {"action":"probe","chain":"solana"},
            {
                "action":"sign_spl_transfer",
                "source":"TEST_SOURCE",
                "destination":"TEST_DESTINATION",
                "mint":"TEST_MINT",
                "amount":1,
                "recent_blockhash":"TEST_BLOCKHASH",
                "commitment":"confirmed",
                "maxRetries":0,
                "dry_run":True,
                "broadcast":False,
            },
        ]

        attempts = []
        for payload in probes:
            result = self._run(payload)
            attempts.append({
                "request": self.sanitize(payload),
                "result": self.sanitize(result),
            })

            if result.get("success"):
                parsed = result.get("result") or {}
                if isinstance(parsed, dict):
                    if any(k in parsed for k in (
                        "signature","public_key","address",
                        "signed_transaction","signed_transaction_hex",
                        "signed_transaction_base64"
                    )):
                        return {
                            "success":True,
                            "status":"compatible_signer_contract_found",
                            "selected_request":self.sanitize(payload),
                            "selected_result":self.sanitize(parsed),
                            "attempts":attempts,
                        }

        return {
            "success":False,
            "status":"no_compatible_signer_contract_confirmed",
            "attempts":attempts,
        }
