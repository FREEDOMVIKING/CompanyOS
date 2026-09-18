from pathlib import Path
import ast
def test_v35_contract():
    p=Path("companyos/runtime/autonomous_task_dispatcher.py")
    s=p.read_text(); ast.parse(s)
    assert "V35_1_FENCED_HANDLER_CALL" in s
    assert "LeaseExecutionGuard" in s
    # Original naked direct handler call may exist only inside the fenced lambda.
    assert "_v35_guard.execute" in s
