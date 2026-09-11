import json, os, urllib.request

class SolanaRpcClient:
    def __init__(self):
        self.url = os.getenv("SOLANA_RPC_URL","").strip()

    def call(self, method, params=None):
        if not self.url:
            return {"success":False,"status":"solana_rpc_missing"}
        req = urllib.request.Request(
            self.url,
            data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or []}).encode(),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode())
            if "error" in data:
                return {"success":False,"status":"rpc_error","error":data["error"]}
            return {"success":True,"result":data.get("result")}
        except Exception as exc:
            return {"success":False,"status":"rpc_exception","error":type(exc).__name__,"message":str(exc)}

    def latest_blockhash(self):
        return self.call("getLatestBlockhash",[{"commitment":"confirmed"}])

    def balance(self, address):
        return self.call("getBalance",[address,{"commitment":"confirmed"}])

    def fee_for_message(self, message_base64):
        return self.call("getFeeForMessage",[message_base64,{"commitment":"confirmed"}])

    def signature_status(self, signature):
        """Return Solana RPC signature status for one transaction signature."""
        return self.call(
            "getSignatureStatuses",
            [[signature], {"searchTransactionHistory": True}]
        )

    def transaction(self, signature):
        """Return confirmed transaction details when available."""
        return self.call(
            "getTransaction",
            [
                signature,
                {
                    "commitment": "confirmed",
                    "maxSupportedTransactionVersion": 0
                }
            ]
        )

    def simulate(self, tx_base64):
        return self.call("simulateTransaction",[
            tx_base64,
            {
                "encoding":"base64",
                "sigVerify":True,
                "replaceRecentBlockhash":False,
                "commitment":"processed"
            }
        ])
