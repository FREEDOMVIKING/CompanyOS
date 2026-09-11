from companyos_phase873_888 import DecisionConvergence, BoundedRoundPolicy, VentureArchiveBridge
def test_convergence():
    h=[{"confidence":.6,"decision":"REVISE"},{"confidence":.605,"decision":"REVISE"}]
    assert DecisionConvergence().evaluate(h)["converged"]
def test_bound():
    assert BoundedRoundPolicy().evaluate(4,3)["allowed"] is False
def test_archive():
    assert VentureArchiveBridge().build("KILL",.2)["archive"] is True
