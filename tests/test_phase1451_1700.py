from companyos.organization import GoalDecomposer, PriorityEngine, ApprovalRouter

def test_goal_decomposition():
    assert len(GoalDecomposer().decompose("build business")) >= 5

def test_priority_engine():
    rows=PriorityEngine().rank([
        {"id":"a","impact":1,"urgency":1,"confidence":.9,"risk":.1,"effort":1},
        {"id":"b","impact":.2,"urgency":.2,"confidence":.5,"risk":.5,"effort":1},
    ])
    assert rows[0]["id"]=="a"

def test_approval_router():
    routed=ApprovalRouter().route([{"kind":"contract_signature"}])
    assert len(routed["approval_queue"])==1
