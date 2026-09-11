class SolanaSimulationGate:
    def evaluate(self, *, rpc_ok, identity_ok, balance_ok, simulation_result=None):
        sim_passed = False
        sim_status = "not_run"
        if simulation_result is not None:
            if simulation_result.get("success"):
                value = (simulation_result.get("result") or {}).get("value") or {}
                sim_passed = value.get("err") is None
                sim_status = "passed" if sim_passed else "failed"
            else:
                sim_status = simulation_result.get("status","failed")

        ready = bool(rpc_ok and identity_ok and balance_ok and sim_passed)
        return {
            "success":True,
            "status":"solana_simulation_gate_evaluated",
            "rpc_ok":bool(rpc_ok),
            "identity_ok":bool(identity_ok),
            "balance_ok":bool(balance_ok),
            "simulation_status":sim_status,
            "simulation_passed":sim_passed,
            "ready_for_live_review":ready,
            "ready_for_live":False,
            "broadcast_attempted":False
        }
