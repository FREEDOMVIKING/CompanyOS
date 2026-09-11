import json, os, urllib.request, base64

class SolanaSimulationValidator:
    def simulate(self, signed_transaction_base64=None):
        if not signed_transaction_base64:
            return {
                "success":True,
                "status":"simulation_skipped_no_serialized_transaction",
                "broadcast_attempted":False,
                "passed":False,
            }

        url = os.getenv("SOLANA_RPC_URL","").strip()
        if not url:
            return {"success":False,"status":"solana_rpc_missing","broadcast_attempted":False}

        payload = {
            "jsonrpc":"2.0",
            "id":1,
            "method":"simulateTransaction",
            "params":[
                signed_transaction_base64,
                {
                    "encoding":"base64",
                    "sigVerify":True,
                    "replaceRecentBlockhash":False,
                    "commitment":"processed"
                }
            ]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data=json.loads(r.read().decode("utf-8"))
            if "error" in data:
                return {
                    "success":False,
                    "status":"simulation_rpc_error",
                    "error":data["error"],
                    "broadcast_attempted":False,
                    "passed":False,
                }
            value=(data.get("result") or {}).get("value") or {}
            err=value.get("err")
            return {
                "success":True,
                "status":"simulation_complete",
                "passed":err is None,
                "err":err,
                "logs":value.get("logs"),
                "units_consumed":value.get("unitsConsumed"),
                "broadcast_attempted":False,
            }
        except Exception as exc:
            return {
                "success":False,
                "status":"simulation_exception",
                "error":type(exc).__name__,
                "message":str(exc),
                "broadcast_attempted":False,
                "passed":False,
            }
