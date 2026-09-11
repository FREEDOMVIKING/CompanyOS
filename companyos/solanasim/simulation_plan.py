class SolanaSimulationPlan:
    def build(self, source, destination, lamports, blockhash):
        return {
            "success":True,
            "status":"solana_nonbroadcast_plan_built",
            "plan":{
                "chain":"solana",
                "source":source,
                "destination":destination,
                "lamports":int(lamports),
                "recent_blockhash":blockhash,
                "broadcast":False,
                "signing_mode":"validation_only"
            }
        }
