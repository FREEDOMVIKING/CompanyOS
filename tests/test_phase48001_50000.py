from companyos.solanasim import SolanaSimulationPlan, SolanaSimulationGate

def test_plan_no_broadcast():
    p=SolanaSimulationPlan().build("A","B",1,"BH")
    assert p["plan"]["broadcast"] is False

def test_gate_requires_simulation():
    g=SolanaSimulationGate().evaluate(rpc_ok=True,identity_ok=True,balance_ok=True,simulation_result=None)
    assert g["ready_for_live_review"] is False

def test_gate_pass():
    g=SolanaSimulationGate().evaluate(
        rpc_ok=True,identity_ok=True,balance_ok=True,
        simulation_result={"success":True,"result":{"value":{"err":None}}}
    )
    assert g["simulation_passed"] is True
