from companyos.runtime.self_evolution_closed_loop import ClosedLoopSelfEvolution

def test_protected_path(tmp_path):
    assert ClosedLoopSelfEvolution(tmp_path).protected("companyos/finance/live.py")

def test_candidate_scores(tmp_path):
    c=ClosedLoopSelfEvolution(tmp_path)
    assert c.score_text(c.candidate_source()) > 0

def test_candidate_has_executable_function(tmp_path):
    assert "def improve_execution_readiness" in ClosedLoopSelfEvolution(tmp_path).candidate_source()

