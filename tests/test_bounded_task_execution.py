import time
from companyos.runtime.bounded_task_execution import run_bounded

def test_success():
    r=run_bounded(lambda: 7, .2)
    assert r.ok and r.value == 7 and not r.timed_out

def test_timeout_is_bounded():
    start=time.monotonic()
    r=run_bounded(lambda: time.sleep(1), .05)
    assert not r.ok and r.timed_out
    assert time.monotonic()-start < .5

def test_exception_is_captured():
    def boom():
        raise ValueError("x")
    r=run_bounded(boom, .2)
    assert not r.ok and "ValueError" in (r.error or "")
