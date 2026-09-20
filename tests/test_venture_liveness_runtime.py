from companyos.runtime.venture_liveness_runtime import (
    orchestration_counts,
    task_counts,
    canonical_summary,
)

def test_orchestration_counts_shape():
    s=orchestration_counts()
    assert set(("RUNNING","COMPLETED","FAILED","HALTED")).issubset(s)

def test_task_counts_shape():
    s=task_counts()
    assert "QUEUED" in s
    assert "FAILED" in s
    assert "business_tasks" in s
    assert "procurement_support_tasks" in s

def test_canonical_summary_shape():
    s=canonical_summary()
    assert "canonical_ventures" in s
    assert "stalled_3plus" in s
