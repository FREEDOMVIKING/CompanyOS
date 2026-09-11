import json, os, urllib.request

class UnsignedPayloadBuilder:
    def _rpc(self, method, params=None):
        url = os.getenv("SOLANA_RPC_URL","").strip()
        if not url:
            return {"success":False,"status":"solana_rpc_missing"}

        req = urllib.request.Request(
            url,
            data=json.dumps({
                "jsonrpc":"2.0","id":1,"method":method,"params":params or []
            }).encode("utf-8"),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            if "error" in data:
                return {"success":False,"status":"rpc_error","error":data["error"]}
            return {"success":True,"result":data.get("result")}
        except Exception as exc:
            return {"success":False,"status":"rpc_exception","error":type(exc).__name__,"message":str(exc)}

    def build(self, source="TEST_SOURCE", destination="TEST_DESTINATION", lamports=1):
        blockhash = self._rpc("getLatestBlockhash", [{"commitment":"confirmed"}])
        if not blockhash.get("success"):
            return {
                "success":False,
                "status":"latest_blockhash_unavailable",
                "rpc":blockhash,
            }

        value = (blockhash.get("result") or {}).get("value") or {}
        return {
            "success":True,
            "status":"unsigned_solana_intent_built",
            "unsigned_intent":{
                "chain":"solana",
                "source":source,
                "destination":destination,
                "lamports":int(lamports),
                "recent_blockhash":value.get("blockhash"),
                "last_valid_block_height":value.get("lastValidBlockHeight"),
                "broadcast":False,
            },
            "note":"This is a validation intent, not a broadcastable transaction serialization."
        }
