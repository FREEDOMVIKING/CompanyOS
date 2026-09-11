from companyos.execution import PersistentWorkerPool, BackpressureController, ExecutionGuardrails

def test_worker_pool(tmp_path):
    p=PersistentWorkerPool(tmp_path)
    p.ensure([{"worker_id":"w","capabilities":["build"]}])
    assert len(p.available("build"))==1

def test_backpressure():
    assert BackpressureController().evaluate(50,2)["throttle"] is True

def test_guardrail():
    assert ExecutionGuardrails().evaluate({"kind":"bank_transfer","amount":1000})["requires_approval"]
