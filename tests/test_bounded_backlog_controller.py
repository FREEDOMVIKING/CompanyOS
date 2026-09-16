from types import SimpleNamespace
from companyos.runtime.bounded_backlog_controller import select_bounded

def t(i,stage="research",priority=100,state="QUEUED"):
    return SimpleNamespace(task_id=str(i),idempotency_key=str(i),state=state,
        priority=priority,created_at_unix=i,payload={"stage":stage})

def test_bounded():
    rows=[t(i) for i in range(5000)]
    x=select_bounded(rows,limit=25,scan_limit=200,budget_seconds=2)
    assert len(x.selected)==25
    assert x.scanned<=200

def test_execution_priority():
    rows=[t(1,"research",1),t(2,"execution",100)]
    x=select_bounded(rows,limit=2,scan_limit=10,budget_seconds=2)
    assert x.selected[0].task_id=="2"

def test_terminal_skipped():
    rows=[t(1,state="COMPLETED"),t(2)]
    x=select_bounded(rows,limit=10,scan_limit=10,budget_seconds=2)
    assert [z.task_id for z in x.selected]==["2"]
