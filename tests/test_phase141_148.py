from companyos_phase141_148 import (
    AutonomousResearcher,
    OperationsAutopilot,
    CodeEvolutionEngine,
    ResourceRebalancer,
)

def test_research_gap_detection():
    rows = AutonomousResearcher().create_missions(
        [{"required_topics":["a","b"]}],
        [{"topic":"a"}],
    )
    assert [x["topic"] for x in rows] == ["b"]

def test_safe_ops_auto_allowed():
    assert OperationsAutopilot().decide(
        [{"proposed_action":"restart_worker"}]
    )[0]["autonomous_action_allowed"] is True

def test_code_evolution_requires_tests():
    result = CodeEvolutionEngine().authorize({"scope":"bug_fix","reversible":True})
    assert result["autonomous_change_allowed"] is True
    assert result["tests_required"] is True

def test_resource_rebalance_internal():
    result = ResourceRebalancer().rebalance(
        [{"name":"x","traction":1,"learning":1,"margin":1,"risk":0}],
        10,
    )
    assert result["autonomous_internal_rebalance"] is True
