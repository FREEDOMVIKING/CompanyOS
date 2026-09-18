from companyos.runtime.execution_drain_engine import ExecutionDrainEngine
def test_batch_bounds():
    assert ExecutionDrainEngine(0).batch_size == 1
    assert ExecutionDrainEngine(999).batch_size == 128
