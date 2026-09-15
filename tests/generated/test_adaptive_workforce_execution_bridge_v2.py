import inspect
from companyos.runtime.adaptive_worker_factory import Factory
from companyos.runtime import adaptive_workforce_execution_bridge as b

def test_factory_real_api():
    assert hasattr(Factory, "cycle")
    assert not hasattr(Factory, "evaluate")

def test_bridge_calls_cycle_not_evaluate():
    src = inspect.getsource(b._invoke_cycle)
    assert ".cycle" in src
    assert ".evaluate" not in src

def test_no_invented_profit_policy():
    src = inspect.getsource(b.cycle)
    assert "financial_metrics_invented" in src
    assert "attributed_profit" in src

def test_module_paths():
    assert b.STATE.name.endswith(".json")
    assert b.RESULTS.name.endswith(".jsonl")
