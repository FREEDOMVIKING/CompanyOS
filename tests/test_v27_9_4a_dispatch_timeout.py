from pathlib import Path

def test_timeout_wiring_present():
    s=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
    assert "V27_9_4A_LIVE_HANDLER_TIMEOUT" in s
    assert "run_bounded(lambda: handler(task))" in s
    assert "TimeoutError" in s
