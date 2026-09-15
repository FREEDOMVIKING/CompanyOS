from companyos.runtime.continuous_profit_improvement_loop import evidence_score, bottlenecks
def test_functions_exist():
    assert callable(evidence_score)
    assert callable(bottlenecks)
def test_no_automatic_profit_invention():
    s,e=evidence_score()
    assert 0 <= s <= 100
def test_policy_source_contains_strict_promotion():
    import inspect
    from companyos.runtime import continuous_profit_improvement_loop as m
    src=inspect.getsource(m)
    assert "verified>=2" in src
    assert "invent_profit" in src
